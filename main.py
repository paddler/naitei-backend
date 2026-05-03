"""Naitei.ai - FastAPI backend for interview preparation SaaS."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import secrets
import subprocess
import tempfile
import time
import uuid
import zipfile
from abc import ABC, abstractmethod
from base64 import b64encode
from enum import Enum
from io import BytesIO
from typing import Any, AsyncIterator, Generic, Optional, TypeVar

import urllib.request
import httpx

# ── Japanese font for PDF generation ──────────────────────────────────────────
# Pre-register at module load so every PDF call reuses the same font object.
_JP_FONT_NAME: str = "Helvetica"  # default (ASCII-only fallback)
_JP_FONT_BOLD: str = "Helvetica-Bold"

def _init_jp_font() -> None:
    """Try to register a CJK-capable font; silently fall back to Helvetica."""
    global _JP_FONT_NAME, _JP_FONT_BOLD
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfbase.ttfonts import TTFont

        # 1. CID built-in (always available in the reportlab package)
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
            _JP_FONT_NAME = "HeiseiKakuGo-W5"
            _JP_FONT_BOLD = "HeiseiKakuGo-W5"
            return
        except Exception:
            pass

        # 2. System / cached TTF
        _cache = "/tmp/NotoSansJP-Regular.ttf"
        candidates = [
            _cache,
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont("NotoSansJP", path))
                    _JP_FONT_NAME = "NotoSansJP"
                    _JP_FONT_BOLD = "NotoSansJP"
                    return
                except Exception:
                    pass

        # 3. Download NotoSansJP static TTF from GitHub
        url = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/static/NotoSansJP-Regular.ttf"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(_cache, "wb") as fh:
            fh.write(data)
        pdfmetrics.registerFont(TTFont("NotoSansJP", _cache))
        _JP_FONT_NAME = "NotoSansJP"
        _JP_FONT_BOLD = "NotoSansJP"
    except Exception:
        pass  # Helvetica fallback remains

_init_jp_font()
# ──────────────────────────────────────────────────────────────────────────────
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from docx import Document as DocxDocument
from PyPDF2 import PdfReader

# Load environment variables from .env file
load_dotenv(dotenv_path="/Users/nabehiro/Desktop/Next_Career 2/.env")

# Parse .env file manually as fallback
def load_env_from_file(filepath: str) -> dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = {}
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return env_vars

# Try to load from file first, then from environment
env_file_path = "/Users/nabehiro/Desktop/Next_Career 2/.env"
env_file_vars = load_env_from_file(env_file_path) if os.path.exists(env_file_path) else {}

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY = env_file_vars.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = env_file_vars.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = env_file_vars.get("GOOGLE_GENERATIVE_AI_API_KEY") or os.getenv("GOOGLE_GENERATIVE_AI_API_KEY", "")
RATE_LIMIT_DISABLED = (env_file_vars.get("RATE_LIMIT_DISABLED") or os.getenv("RATE_LIMIT_DISABLED", "")).lower() == "true"
DEFAULT_PROVIDER = env_file_vars.get("AI_PROVIDER") or os.getenv("AI_PROVIDER", "claude")
FALLBACK_ORDER: list[str] = (env_file_vars.get("AI_FALLBACK_ORDER") or os.getenv("AI_FALLBACK_ORDER", "claude,openai,gemini")).split(",")

# ---------------------------------------------------------------------------
# Pydantic Models  (CRITICAL #1: SessionState, CRITICAL #2: InterviewMaterials)
# ---------------------------------------------------------------------------

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class CareerEntry(CamelModel):
    company: str
    period_from: str = Field(alias="periodFrom")
    period_to: Optional[str] = Field(None, alias="periodTo")
    role: str
    achievements: list[str] = []


class ApplicantProfile(CamelModel):
    name: str
    age: Optional[int] = Field(None, ge=15, le=99)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    career_history: list[CareerEntry] = Field(default_factory=list, alias="careerHistory")
    qualifications: list[str] = []
    self_pr: Optional[str] = Field(None, alias="selfPr")
    raw_text: str = Field("", alias="rawText")


class CompanyInfo(CamelModel):
    name: str
    url: Optional[str] = None
    job_title: str = Field("", alias="jobTitle")
    job_description: str = Field("", alias="jobDescription")
    requirements: list[str] = []
    preferred_skills: list[str] = Field(default_factory=list, alias="preferredSkills")
    employment_type: Optional[str] = Field(None, alias="employmentType")
    salary: Optional[str] = None
    selection_flow: list[str] = Field(default_factory=list, alias="selectionFlow")
    raw_text: str = Field("", alias="rawText")


class MarkdownDoc(CamelModel):
    markdown: str


class InterviewMaterials(CamelModel):
    qa: Optional[MarkdownDoc] = None
    pr: Optional[MarkdownDoc] = None
    questions: Optional[MarkdownDoc] = None
    checklist: Optional[MarkdownDoc] = None


class ReviewComment(CamelModel):
    section: str
    severity: str
    message: str


class ReviewData(CamelModel):
    resume: Optional[str] = None
    career_history: Optional[str] = Field(None, alias="careerHistory")
    comments: list[ReviewComment] = []


class ChatMessage(CamelModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class InterviewState(CamelModel):
    qa: Optional[str] = None
    pr: Optional[str] = None
    questions: Optional[str] = None
    checklist: Optional[str] = None
    chat_history: list[ChatMessage] = Field(default_factory=list, alias="chatHistory")


class Preferences(CamelModel):
    ai_provider: str = Field("claude", alias="aiProvider")
    tier: str = "balanced"


class SessionState(CamelModel):
    version: int = 1
    created_at: str = Field("", alias="createdAt")
    updated_at: str = Field("", alias="updatedAt")
    current_step: str = Field("step1", alias="currentStep")
    applicant: Optional[ApplicantProfile] = None
    company: Optional[CompanyInfo] = None
    review: Optional[ReviewData] = None
    interview: Optional[InterviewState] = None
    preferences: Preferences = Field(default_factory=Preferences)


class UsageInfo(CamelModel):
    prompt_tokens: int = Field(0, alias="promptTokens")
    completion_tokens: int = Field(0, alias="completionTokens")
    total_tokens: int = Field(0, alias="totalTokens")
    cost_usd: Optional[float] = Field(None, alias="costUsd")


class ApiMeta(CamelModel):
    request_id: str = Field("", alias="requestId")
    latency_ms: Optional[float] = Field(None, alias="latencyMs")
    usage: Optional[UsageInfo] = None
    model: Optional[str] = None
    provider: Optional[str] = None


T = TypeVar("T")


class ApiSuccess(CamelModel, Generic[T]):
    success: bool = True
    data: T
    error: None = None
    meta: Optional[ApiMeta] = None


class ApiError(CamelModel):
    success: bool = False
    data: None = None
    error: str
    meta: Optional[ApiMeta] = None


# --- Request models ---

class ScrapeRequest(CamelModel):
    url: str


class ExtractRequest(CamelModel):
    pass


class ReviewRequest(CamelModel):
    applicant: ApplicantProfile
    company: CompanyInfo
    target: str = "both"
    tone: str = "standard"


class InterviewGenRequest(CamelModel):
    applicant: ApplicantProfile
    company: CompanyInfo
    interviewer_profile: Optional[str] = Field(None, alias="interviewerProfile")


class ChatRequest(CamelModel):
    applicant: ApplicantProfile
    company: CompanyInfo
    messages: list[ChatMessage] = []


class PdfRequest(CamelModel):
    materials: InterviewMaterials
    applicant_name: str = Field("", alias="applicantName")
    company_name: str = Field("", alias="companyName")
    interview_date: Optional[str] = Field(None, alias="interviewDate")
    job_title: str = Field("", alias="jobTitle")


class ResearchRequest(CamelModel):
    company: CompanyInfo


# ---------------------------------------------------------------------------
# PII Masker  (HIGH #6)
# ---------------------------------------------------------------------------

class PIIMasker:
    _PATTERNS: list[tuple[str, re.Pattern[str]]] = [
        ("EMAIL", re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")),
        ("PHONE", re.compile(r"0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}")),
        ("POSTAL", re.compile(r"\d{3}-?\d{4}")),
        # BIRTHDAY: Match Japanese date formats (日付記載) but NOT ISO format (YYYY-MM-DD used in APIs)
        # Negative lookahead (?!.*\d-\d) to exclude patterns like "2025-06-01"
        ("BIRTHDAY", re.compile(
            r"(19|20)\d{2}[/年](0?[1-9]|1[0-2])[/月](0?[1-9]|[12]\d|3[01])日?"
        )),
        ("NAME_JP", re.compile(
            r"(?:氏名|名前)\s*[:：]\s*[　-鿿]{1,4}\s*[　-鿿]{1,4}"
        )),
    ]

    @classmethod
    def mask(cls, text: str) -> str:
        for label, pattern in cls._PATTERNS:
            text = pattern.sub(f"[{label}_MASKED]", text)
        return text


# ---------------------------------------------------------------------------
# Token Bucket Rate Limiter  (HIGH #5)
# ---------------------------------------------------------------------------

_RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/api/scrape": (10, 600),
    "/api/extract": (20, 600),
    "/api/review": (10, 600),
    "/api/pdf": (30, 600),
    "/api/interview": (60, 600),
    "/api/research": (5, 600),
}

_buckets: dict[str, dict[str, float]] = {}


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str, path: str) -> tuple[bool, int, float]:
    prefix = path
    for key in _RATE_LIMITS:
        if path.startswith(key):
            prefix = key
            break
    else:
        return True, 0, 0.0

    limit, window = _RATE_LIMITS[prefix]
    bucket_key = f"{ip}:{prefix}"
    now = time.monotonic()
    bucket = _buckets.get(bucket_key, {"tokens": float(limit), "last": now})
    elapsed = now - bucket["last"]
    bucket["tokens"] = min(float(limit), bucket["tokens"] + (elapsed / window) * limit)
    bucket["last"] = now

    if bucket["tokens"] < 1.0:
        retry_after = (1.0 - bucket["tokens"]) / (limit / window)
        _buckets[bucket_key] = bucket
        return False, limit, retry_after

    bucket["tokens"] -= 1.0
    _buckets[bucket_key] = bucket
    return True, limit, 0.0


# ---------------------------------------------------------------------------
# SSRF Protection
# ---------------------------------------------------------------------------

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
]


def _is_safe_url(url: str) -> bool:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        import socket
        resolved = socket.getaddrinfo(hostname, None)
        for _, _, _, _, addr in resolved:
            ip = ipaddress.ip_address(addr[0])
            for net in _PRIVATE_NETWORKS:
                if ip in net:
                    return False
    except (socket.gaierror, ValueError):
        return False
    return True


# ---------------------------------------------------------------------------
# Magic Byte File Validation
# ---------------------------------------------------------------------------

MAGIC_BYTES: dict[str, bytes] = {
    "application/pdf": b"%PDF",
    "image/png": b"\x89PNG",
    "image/jpeg": b"\xff\xd8\xff",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_upload(content: bytes, content_type: str) -> None:
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File exceeds 10MB limit")
    expected = MAGIC_BYTES.get(content_type)
    if expected and not content[: len(expected)] == expected:
        raise HTTPException(422, "File signature does not match declared MIME type")


# ---------------------------------------------------------------------------
# File Text Extraction
# ---------------------------------------------------------------------------

def extract_text_from_file(content: bytes, content_type: str) -> str:
    """Extract text from DOCX, PDF, or plain text files."""
    try:
        if content_type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/x-docx"):
            # Extract text from DOCX
            doc = DocxDocument(BytesIO(content))
            text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
            # Also extract table content
            for table in doc.tables:
                for row in table.rows:
                    text += "\n" + " | ".join(cell.text for cell in row.cells)
            return text.strip()
        elif content_type in ("application/pdf", "text/plain"):
            # Extract text from PDF
            if content_type == "application/pdf":
                pdf_reader = PdfReader(BytesIO(content))
                text = "\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
            else:
                # Plain text
                text = content.decode("utf-8", errors="replace")
            return text.strip()
        else:
            # Default: try to decode as text
            return content.decode("utf-8", errors="replace").strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from file: {str(e)}")


# ---------------------------------------------------------------------------
# API Response Helpers
# ---------------------------------------------------------------------------

def ok(data: Any, *, request_id: str = "", latency_ms: float = 0, **meta_kw: Any) -> dict:
    meta = {"requestId": request_id, "latencyMs": latency_ms, **meta_kw}
    return {"success": True, "data": data, "error": None, "meta": meta}


def err(message: str, *, status: int = 400, request_id: str = "") -> JSONResponse:
    body = {"success": False, "data": None, "error": PIIMasker.mask(message), "meta": {"requestId": request_id}}
    return JSONResponse(body, status_code=status)


# ---------------------------------------------------------------------------
# AIProvider ABC + Implementations  (Cascade Fallback)
# ---------------------------------------------------------------------------

class TaskKind(str, Enum):
    EXTRACT_JOB = "extract_job_posting"
    EXTRACT_RESUME = "extract_resume"
    REVIEW = "review_document"
    GEN_QA = "generate_qa"
    GEN_PR = "generate_self_pr"
    GEN_QUESTIONS = "generate_counter_questions"
    GEN_CHECKLIST = "generate_checklist"
    COMPANY_RESEARCH = "company_research"
    CHAT = "chat"


MODEL_MAP: dict[str, dict[TaskKind, str]] = {
    "claude": {
        TaskKind.EXTRACT_JOB: "claude-haiku-4-5",
        TaskKind.EXTRACT_RESUME: "claude-haiku-4-5",
        TaskKind.REVIEW: "claude-haiku-4-5",
        TaskKind.GEN_QA: "claude-haiku-4-5",
        TaskKind.GEN_PR: "claude-haiku-4-5",
        TaskKind.GEN_QUESTIONS: "claude-haiku-4-5",
        TaskKind.GEN_CHECKLIST: "claude-haiku-4-5",
        TaskKind.COMPANY_RESEARCH: "claude-haiku-4-5",
        TaskKind.CHAT: "claude-haiku-4-5",
    },
    "openai": {k: "gpt-4o" for k in TaskKind},
    "gemini": {k: "gemini-2.5-flash" for k in TaskKind},
}


class AIProvider(ABC):
    name: str

    @abstractmethod
    async def generate_text(self, prompt: str, *, system: str = "", model: str = "", **kw: Any) -> dict:
        ...

    @abstractmethod
    async def stream_text(self, prompt: str, *, system: str = "", model: str = "", **kw: Any) -> AsyncIterator[dict]:
        ...

    @abstractmethod
    async def generate_from_image(self, image: bytes, mime: str, prompt: str, *, model: str = "", **kw: Any) -> dict:
        ...


class ClaudeProvider(AIProvider):
    name = "claude"

    async def generate_text(self, prompt: str, *, system: str = "", model: str = "claude-haiku-4-5", **kw: Any) -> dict:
        # Adjust max_tokens based on model
        max_tokens = 2048 if "haiku" in model else 4096

        # Create explicit http_client to avoid deprecated proxies parameter issue
        http_client = httpx.AsyncClient(timeout=120)
        try:
            client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY, http_client=http_client)
            print(f"[DEBUG] AsyncAnthropic client created successfully")
        except Exception as e:
            print(f"[ERROR] Failed to create AsyncAnthropic client: {e}")
            await http_client.aclose()
            raise

        try:
            # Build system messages if provided
            system_blocks = None
            if system:
                system_blocks = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]

            # Call Anthropic API using SDK
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_blocks if system_blocks else None,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract text from response
            text = "".join(b.text for b in response.content if b.type == "text")
            return {"text": text, "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}}
        finally:
            await http_client.aclose()

    async def stream_text(self, prompt: str, *, system: str = "", model: str = "claude-haiku-4-5", **kw: Any) -> AsyncIterator[dict]:
        # Adjust max_tokens based on model
        max_tokens = 2048 if "haiku" in model else 4096

        # Create explicit http_client to avoid deprecated proxies parameter issue
        http_client = httpx.AsyncClient(timeout=120)
        try:
            client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY, http_client=http_client)
            print(f"[DEBUG] AsyncAnthropic client created successfully")
        except Exception as e:
            print(f"[ERROR] Failed to create AsyncAnthropic client: {e}")
            await http_client.aclose()
            raise

        print(f"[DEBUG ClaudeProvider.stream_text] Sending request to Anthropic API:")
        print(f"  Model: {model}")
        print(f"  API Key: {ANTHROPIC_API_KEY[:30]}...{ANTHROPIC_API_KEY[-20:]}")
        print(f"  System: {system[:100] if system else 'None'}...")
        print(f"  Prompt length: {len(prompt)}")

        # Build system messages if provided
        system_param = None
        if system:
            system_param = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]

        # Use SDK streaming with async context manager - automatically handles version negotiation
        try:
            print(f"[DEBUG] Starting messages.stream with model={model}, max_tokens={max_tokens}")
            async with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                system=system_param if system_param else None,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                print(f"[DEBUG] Stream context manager entered successfully")
                # Stream text deltas
                async for text in stream.text_stream:
                    if text:
                        yield {"type": "text-delta", "delta": text}
                print(f"[DEBUG] Stream text_stream iteration completed")
                # get_final_message は with ブロック内で呼ぶ（ブロック外では無効になる場合がある）
                try:
                    final_message = await stream.get_final_message()
                    yield {"type": "finish", "usage": {"input_tokens": final_message.usage.input_tokens, "output_tokens": final_message.usage.output_tokens}}
                except Exception:
                    yield {"type": "finish", "usage": {}}
        except Exception as e:
            print(f"[ERROR] Exception during streaming: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await http_client.aclose()

    async def generate_from_image(self, image: bytes, mime: str, prompt: str, *, model: str = "claude-haiku-4-5", **kw: Any) -> dict:
        # Adjust max_tokens based on model
        max_tokens = 2048 if "haiku" in model else 4096
        http_client = httpx.AsyncClient(timeout=120)
        try:
            client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY, http_client=http_client)

            # Encode image to base64
            b64 = b64encode(image).decode()

            # Call Anthropic API using SDK with image
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}},
                        {"type": "text", "text": prompt},
                    ]
                }]
            )

            # Extract text from response
            text = "".join(b.text for b in response.content if b.type == "text")
            return {"text": text, "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}}
        finally:
            await http_client.aclose()


class OpenAIProvider(AIProvider):
    name = "openai"

    async def _chat(self, messages: list[dict], *, model: str, stream: bool = False, **kw: Any) -> httpx.Response:
        async with httpx.AsyncClient(timeout=120) as c:
            return await c.post("https://api.openai.com/v1/chat/completions", json={
                "model": model, "messages": messages, "stream": stream, **kw,
            }, headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"})

    async def generate_text(self, prompt: str, *, system: str = "", model: str = "gpt-4o", **kw: Any) -> dict:
        msgs: list[dict] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        r = await self._chat(msgs, model=model)
        r.raise_for_status()
        data = r.json()
        return {"text": data["choices"][0]["message"]["content"], "usage": data.get("usage", {})}

    async def stream_text(self, prompt: str, *, system: str = "", model: str = "gpt-4o", **kw: Any) -> AsyncIterator[dict]:
        msgs: list[dict] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        async with httpx.AsyncClient(timeout=120) as c:
            async with c.stream("POST", "https://api.openai.com/v1/chat/completions", json={
                "model": model, "messages": msgs, "stream": True,
            }, headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: ") or line.strip() == "data: [DONE]":
                        continue
                    chunk = json.loads(line[6:])
                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        yield {"type": "text-delta", "delta": delta}
        yield {"type": "finish", "usage": {}}

    async def generate_from_image(self, image: bytes, mime: str, prompt: str, *, model: str = "gpt-4o", **kw: Any) -> dict:
        b64 = b64encode(image).decode()
        msgs = [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            {"type": "text", "text": prompt},
        ]}]
        r = await self._chat(msgs, model=model)
        r.raise_for_status()
        data = r.json()
        return {"text": data["choices"][0]["message"]["content"], "usage": data.get("usage", {})}


class GeminiProvider(AIProvider):
    name = "gemini"

    async def generate_text(self, prompt: str, *, system: str = "", model: str = "gemini-2.5-flash", **kw: Any) -> dict:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GOOGLE_API_KEY}"
        parts: list[dict] = []
        if system:
            parts.append({"text": system})
        parts.append({"text": prompt})
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(url, json={"contents": [{"parts": parts}]})
            r.raise_for_status()
            data = r.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return {"text": text, "usage": data.get("usageMetadata", {})}

    async def stream_text(self, prompt: str, *, system: str = "", model: str = "gemini-2.5-flash", **kw: Any) -> AsyncIterator[dict]:
        result = await self.generate_text(prompt, system=system, model=model)
        yield {"type": "text-delta", "delta": result["text"]}
        yield {"type": "finish", "usage": result.get("usage", {})}

    async def generate_from_image(self, image: bytes, mime: str, prompt: str, *, model: str = "gemini-2.5-flash", **kw: Any) -> dict:
        b64 = b64encode(image).decode()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GOOGLE_API_KEY}"
        parts = [{"inline_data": {"mime_type": mime, "data": b64}}, {"text": prompt}]
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(url, json={"contents": [{"parts": parts}]})
            r.raise_for_status()
            data = r.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return {"text": text, "usage": data.get("usageMetadata", {})}


_PROVIDERS: dict[str, AIProvider] = {
    "claude": ClaudeProvider(),
    "openai": OpenAIProvider(),
    "gemini": GeminiProvider(),
}


def get_provider(name: str | None = None) -> AIProvider:
    return _PROVIDERS[name or DEFAULT_PROVIDER]


async def with_fallback(fn, *, skip: list[str] | None = None):
    last_err: Exception | None = None
    for name in FALLBACK_ORDER:
        if skip and name in skip:
            continue
        try:
            return await fn(_PROVIDERS[name])
        except (httpx.HTTPStatusError, httpx.ConnectError) as e:
            last_err = e
            status = getattr(e, "response", None)
            if status and status.status_code not in (429, 500, 502, 503):
                raise
    raise last_err or RuntimeError("No AI providers available")


# ---------------------------------------------------------------------------
# SSE Streaming Helper
# ---------------------------------------------------------------------------

async def sse_stream(provider: AIProvider, prompt: str, system: str, task: TaskKind, request_id: str):
    model = MODEL_MAP.get(provider.name, {}).get(task, "")

    async def generate():
        try:
            async for chunk in provider.stream_text(prompt, system=system, model=model):
                if chunk["type"] == "text-delta":
                    masked = PIIMasker.mask(chunk["delta"])
                    yield f"event: content\ndata: {json.dumps({'type': 'content', 'delta': masked})}\n\n"
                elif chunk["type"] == "finish":
                    yield f"event: done\ndata: {json.dumps({'type': 'done', 'usage': chunk.get('usage', {}), 'requestId': request_id})}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': PIIMasker.mask(str(exc))})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache", "X-Request-Id": request_id,
    })


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(title="Naitei.ai", version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# Global exception handler — ensures all unhandled exceptions return JSON (not plain text)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    rid = getattr(request.state, "request_id", "")
    return JSONResponse(
        {"success": False, "data": None, "error": f"Internal server error: {type(exc).__name__}", "meta": {"requestId": rid}},
        status_code=500,
    )


# --- CSP Nonce + Security Headers Middleware (CRITICAL #4) ---

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    nonce = secrets.token_urlsafe(16)
    request.state.csp_nonce = nonce
    start = time.monotonic()

    if not RATE_LIMIT_DISABLED and request.url.path.startswith("/api/"):
        ip = _get_client_ip(request)
        allowed, limit, retry_after = _check_rate_limit(ip, request.url.path)
        if not allowed:
            return JSONResponse(
                {"success": False, "data": None, "error": "Rate limit exceeded", "meta": {"requestId": request_id}},
                status_code=429,
                headers={"Retry-After": str(int(retry_after) + 1), "X-RateLimit-Limit": str(limit)},
            )

    response = await call_next(request)
    elapsed = (time.monotonic() - start) * 1000

    if not request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
        response.headers["Content-Security-Policy"] = (
            f"default-src 'self'; "
            f"script-src 'nonce-{nonce}' 'strict-dynamic'; "
            f"style-src 'self' 'nonce-{nonce}'; "
            f"img-src 'self' data: https:; "
            f"font-src 'self' data:; "
            f"connect-src 'self' https://api.anthropic.com https://api.openai.com https://generativelanguage.googleapis.com; "
            f"frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
        )
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Response-Time"] = f"{elapsed:.0f}ms"
    return response


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/scrape")
async def scrape(body: ScrapeRequest, request: Request):
    rid = request.state.request_id
    if not _is_safe_url(body.url):
        return err("URL is not allowed (must be HTTPS, non-private)", status=422, request_id=rid)
    start = time.monotonic()
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
        try:
            r = await c.get(body.url, headers={"User-Agent": "Naitei.ai/0.1"})
            r.raise_for_status()
        except httpx.HTTPError as e:
            return err(f"Failed to fetch URL: {e}", status=502, request_id=rid)
    provider = get_provider()
    model = MODEL_MAP.get(provider.name, {}).get(TaskKind.EXTRACT_JOB, "")
    result = await provider.generate_text(
        f"Extract structured job posting information from the following HTML/text. Return JSON with fields: jobTitle, company, requirements, preferredSkills, employmentType, salary, jobDescription.\n\n{r.text[:15000]}",
        system="You are a job posting extraction specialist. Return valid JSON only.",
        model=model,
    )
    elapsed = (time.monotonic() - start) * 1000
    return ok({"raw_text": r.text[:5000], "structured": result["text"]}, request_id=rid, latency_ms=elapsed, provider=provider.name, model=model)


@app.post("/api/extract")
async def extract(request: Request, file: UploadFile):
    rid = request.state.request_id
    content = await file.read()
    validate_upload(content, file.content_type or "application/octet-stream")

    # Extract text from file (DOCX, PDF, or plain text)
    try:
        file_text = extract_text_from_file(content, file.content_type or "text/plain")
    except ValueError as e:
        return err(f"File extraction failed: {str(e)}", status=422, request_id=rid)

    if not file_text:
        return err("Uploaded file appears to be empty", status=422, request_id=rid)

    provider = get_provider()
    model = MODEL_MAP.get(provider.name, {}).get(TaskKind.EXTRACT_RESUME, "")

    # Use generate_text() with extracted file content
    prompt = f"""Extract applicant profile from the following document content.
Return ONLY a JSON object (no markdown, no code blocks) with these exact fields:
- name (string, required)
- age (number or null)
- careerHistory (array of objects with: company, periodFrom, periodTo, role, achievements)
- qualifications (array of strings or null)
- selfPr (string or null)

Document content:
{file_text[:4000]}"""  # Limit to 4000 chars to avoid token overrun

    try:
        result = await provider.generate_text(prompt, model=model)
    except Exception as e:
        # AI failed but we still have the raw file text — return a minimal profile so step3 can proceed
        fallback = ApplicantProfile(name="", raw_text=file_text[:4000])
        content_type = file.content_type or "text/plain"
        return ok({
            "applicant": fallback.model_dump(by_alias=True),
            "sources": [{"fileName": file.filename or "uploaded-file", "mimeType": content_type, "pageCount": 1, "extractionMethod": "fallback-raw"}],
            "warnings": [f"AI extraction failed ({type(e).__name__}), raw text preserved for review"]
        }, request_id=rid, provider=provider.name, model=model)

    # Parse LLM output as JSON and validate structure
    llm_text = result["text"].strip()
    applicant_data = None

    try:
        # Try to extract JSON from LLM output (may be wrapped in markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', llm_text)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = llm_text

        parsed = json.loads(json_str)

        # Validate against ApplicantProfile schema
        # Inject rawText from actual file content so frontend can use it for review
        parsed["rawText"] = file_text[:4000]
        applicant_data = ApplicantProfile(**parsed)
    except (json.JSONDecodeError, ValueError) as e:
        # If JSON parsing fails, return error with raw text for debugging
        return err(f"Failed to parse extracted data as JSON: {str(e)}", status=422, request_id=rid)
    except Exception as e:
        return err(f"Failed to validate extracted data: {str(e)}", status=422, request_id=rid)

    # Determine extraction method based on file type
    content_type = file.content_type or "text/plain"
    if "pdf" in content_type.lower():
        extraction_method = "pdf-text"
    elif "wordprocessingml" in content_type.lower() or "docx" in content_type.lower():
        extraction_method = "docx-text"
    else:
        extraction_method = "text"

    # Return success with complete ExtractResponse structure
    return ok({
        "applicant": applicant_data.model_dump(by_alias=True),
        "sources": [{
            "fileName": file.filename or "uploaded-file",
            "mimeType": content_type,
            "pageCount": 1,
            "extractionMethod": extraction_method
        }],
        "warnings": []
    }, request_id=rid, provider=provider.name, model=model)


@app.post("/api/review")
async def review(body: ReviewRequest, request: Request):
    rid = request.state.request_id
    provider = get_provider()
    applicant = body.applicant
    company = body.company
    # Use rawText as fallback if structured fields are empty
    applicant_text = (
        applicant.raw_text
        or applicant.self_pr
        or (", ".join(f"{c.role} at {c.company}" for c in applicant.career_history) if applicant.career_history else "")
        or "(応募者情報なし)"
    )
    company_text = (
        company.raw_text
        or company.job_description
        or f"{company.name} {company.job_title}".strip()
        or "(求人情報なし)"
    )
    prompt = (
        f"【応募者情報】\n{applicant_text[:3000]}\n\n"
        f"【求人情報】\n{company_text[:2000]}\n\n"
        f"ターゲット: {body.target}, トーン: {body.tone}\n\n"
        "上記の応募者の職務経歴書・志望動機を、求人要件に合わせて日本語で添削してください。"
        "改善後のテキスト、具体的な変更点、コメント（重要度別）、適合度スコア（0-100）、総評を提供してください。"
        "応募者情報や求人情報が不完全でも、提供された情報をもとに最善の添削を行ってください。"
    )
    return await sse_stream(provider, prompt, "あなたは日本の就職・転職支援の専門家です。応募者の書類を丁寧に添削します。", TaskKind.REVIEW, rid)


@app.post("/api/interview/qa")
async def interview_qa(body: InterviewGenRequest, request: Request):
    rid = request.state.request_id
    provider = get_provider()
    prompt = (
        f"Applicant: {body.applicant.model_dump_json(by_alias=True)}\n"
        f"Company: {body.company.model_dump_json(by_alias=True)}\n"
        f"Interviewer: {body.interviewer_profile or 'Unknown'}\n"
        "Generate 30+ interview Q&A in categories A-H (intro, motivation, career, job-specific, fit, risk, values, closing). "
        "Use STAR/PREP format, 30-90 second spoken Japanese, include applicant-specific episodes."
    )
    return await sse_stream(provider, prompt, "You are a Japanese interview preparation expert.", TaskKind.GEN_QA, rid)


@app.post("/api/interview/pr")
async def interview_pr(body: InterviewGenRequest, request: Request):
    rid = request.state.request_id
    provider = get_provider()
    prompt = (
        f"Applicant: {body.applicant.model_dump_json(by_alias=True)}\n"
        f"Company: {body.company.model_dump_json(by_alias=True)}\n"
        "Generate self-PR in 3 versions: 60-second (~350 chars), 90-second (~500 chars), 3-minute (~900 chars). "
        "Include core strength phrase, 3 career pillars, requirement mapping table, and NG expressions list."
    )
    return await sse_stream(provider, prompt, "You are a Japanese self-PR writing expert.", TaskKind.GEN_PR, rid)


@app.post("/api/interview/questions")
async def interview_questions(body: InterviewGenRequest, request: Request):
    rid = request.state.request_id
    provider = get_provider()
    prompt = (
        f"Applicant: {body.applicant.model_dump_json(by_alias=True)}\n"
        f"Company: {body.company.model_dump_json(by_alias=True)}\n"
        "Generate 10+ reverse questions by category (business understanding, contribution, org understanding, long-term). "
        "Include purpose for each, NG questions list, and usage strategy by time/interviewer type."
    )
    return await sse_stream(provider, prompt, "You are a Japanese interview reverse-question specialist.", TaskKind.GEN_QUESTIONS, rid)


@app.post("/api/interview/checklist")
async def interview_checklist(body: InterviewGenRequest, request: Request):
    rid = request.state.request_id
    provider = get_provider()
    prompt = (
        f"Applicant: {body.applicant.model_dump_json(by_alias=True)}\n"
        f"Company: {body.company.model_dump_json(by_alias=True)}\n"
        "Generate interview preparation checklist covering 7 phases: 3 days before, day before, morning of, "
        "entering/exiting, during interview, after interview, waiting period. Include emergency procedures."
    )
    return await sse_stream(provider, prompt, "You are a Japanese interview preparation coach.", TaskKind.GEN_CHECKLIST, rid)


@app.post("/api/interview/chat")
async def interview_chat(body: ChatRequest, request: Request):
    rid = request.state.request_id
    provider = get_provider()
    history = "\n".join(f"[{m.role}]: {m.content}" for m in body.messages)
    prompt = (
        f"Applicant: {body.applicant.model_dump_json(by_alias=True)}\n"
        f"Company: {body.company.model_dump_json(by_alias=True)}\n"
        f"Conversation:\n{history}\n"
        "Continue the interview coaching conversation. Help the applicant deepen their answers."
    )
    return await sse_stream(provider, prompt, "You are an interactive interview coach for Japanese job seekers.", TaskKind.CHAT, rid)


@app.post("/api/research")
async def research(body: ResearchRequest, request: Request):
    rid = request.state.request_id
    provider = get_provider()
    prompt = (
        f"Company: {body.company.model_dump_json(by_alias=True)}\n"
        "Research this company thoroughly: mission/vision/values, recent news, industry trends, "
        "competitors, work culture, interview tendencies, and ideal candidate profile."
    )
    return await sse_stream(provider, prompt, "You are a thorough company research analyst for Japanese job market.", TaskKind.COMPANY_RESEARCH, rid)


# --- /api/pdf  (ReportLab ベース PDF 生成) ---

def _markdown_to_pdf_bytes(title: str, markdown_text: str, header: str, footer: str) -> bytes:
    """マークダウンテキストを ReportLab で PDF バイト列に変換する。"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

    # Use globally pre-registered font (set at module startup by _init_jp_font)
    font_name = _JP_FONT_NAME
    bold_font = _JP_FONT_BOLD

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=25 * mm, bottomMargin=25 * mm,
    )

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(
        "jp_normal", parent=styles["Normal"],
        fontName=font_name, fontSize=10, leading=16, spaceAfter=4,
    )
    style_h1 = ParagraphStyle(
        "jp_h1", parent=styles["Heading1"],
        fontName=bold_font, fontSize=16, leading=22, spaceBefore=12, spaceAfter=6,
        textColor=colors.HexColor("#0b1e4d"),
    )
    style_h2 = ParagraphStyle(
        "jp_h2", parent=styles["Heading2"],
        fontName=bold_font, fontSize=13, leading=18, spaceBefore=10, spaceAfter=4,
        textColor=colors.HexColor("#1e40af"),
    )
    style_h3 = ParagraphStyle(
        "jp_h3", parent=styles["Heading3"],
        fontName=bold_font, fontSize=11, leading=16, spaceBefore=8, spaceAfter=3,
        textColor=colors.HexColor("#374151"),
    )
    style_header = ParagraphStyle(
        "jp_header", parent=styles["Normal"],
        fontName=bold_font, fontSize=8, textColor=colors.gray, alignment=1,
    )

    story = []
    # Page header
    story.append(Paragraph(header, style_header))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6")))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(title, style_h1))
    story.append(Spacer(1, 4 * mm))

    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 3 * mm))
            continue
        # Escape XML special chars for ReportLab
        safe = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if stripped.startswith("### "):
            story.append(Paragraph(safe[4:], style_h3))
        elif stripped.startswith("## "):
            story.append(Paragraph(safe[3:], style_h2))
        elif stripped.startswith("# "):
            story.append(Paragraph(safe[2:], style_h1))
        elif stripped.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Spacer(1, 2 * mm))
        else:
            # Bold (**text**) simple conversion
            safe = safe.replace("**", "<b>", 1) if "**" in safe else safe
            safe = safe.replace("**", "</b>", 1) if "**" in safe else safe
            story.append(Paragraph(safe, style_normal))

    # Page footer
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph(footer, style_header))

    doc.build(story)
    return buf.getvalue()


@app.post("/api/pdf")
async def generate_pdf(body: PdfRequest, request: Request):
    rid = request.state.request_id
    files_map = {
        "01_添削レポート": body.materials.qa,
        "02_自己PR案": body.materials.pr,
        "03_逆質問集": body.materials.questions,
        "04_事前準備チェックリスト": body.materials.checklist,
    }

    present = {k: v for k, v in files_map.items() if v is not None}
    if not present:
        return err("No interview materials provided", status=422, request_id=rid)

    header = f"{body.company_name or '面接対策'} | {body.applicant_name or ''}"
    footer = f"{body.applicant_name or ''} | {body.interview_date or 'TBD'} | {body.job_title or ''}"

    def _content_disposition(filename: str, ext: str) -> str:
        """RFC 5987 encoded Content-Disposition header for non-ASCII filenames."""
        from urllib.parse import quote
        encoded = quote(f"{filename}{ext}", encoding="utf-8")
        ascii_fallback = filename.encode("ascii", errors="replace").decode() + ext
        return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded}"

    try:
        # 1ファイルの場合はPDFを直接返す。複数の場合はZIPにまとめる
        if len(present) == 1:
            name, doc = next(iter(present.items()))
            pdf_bytes = _markdown_to_pdf_bytes(name, doc.markdown, header, footer)
            return StreamingResponse(
                BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": _content_disposition(name, ".pdf"),
                    "X-Request-Id": rid,
                },
            )

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, doc in present.items():
                pdf_bytes = _markdown_to_pdf_bytes(name, doc.markdown, header, footer)
                zf.writestr(f"{name}.pdf", pdf_bytes)
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="interview_materials.zip"',
                "X-Request-Id": rid,
            },
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return err(f"PDF generation failed: {type(e).__name__}: {str(e)[:300]}\nTraceback:\n{tb[-800:]}", status=500, request_id=rid)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
