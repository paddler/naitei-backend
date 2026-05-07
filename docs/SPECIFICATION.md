# Naitei.ai (NextCareer) - System Specification

Version: 1.0
Last Updated: 2026-05-05

---

## 1. System Overview

Naitei.ai is a Japanese job application support web service that provides AI-powered document review and interview preparation. The system operates as a 4-step wizard guiding users through job posting input, applicant profile creation, document review/correction, and interview preparation.

### 1.1 Architecture Topology

```
[Browser]
    |
    | HTTPS
    v
[Vercel] ── Next.js 14 App Router (Frontend + API Routes)
    |
    | HTTPS (server-to-server)
    v
[Railway] ── FastAPI (Python backend)
    |
    | HTTPS
    v
[AI Providers] ── Claude API / OpenAI API / Gemini API
```

| Layer | Technology | Deployment |
|---|---|---|
| Frontend | Next.js 14 (App Router), React 18, TypeScript 5 | Vercel |
| API Proxy | Next.js API Routes (`app/api/*/route.ts`) | Vercel (same deployment) |
| Backend | FastAPI (Python), Pydantic v2 | Railway |
| AI | Claude (claude-haiku-4-5), OpenAI (gpt-4o), Gemini (gemini-2.5-flash) | External APIs |
| PDF | ReportLab + Japanese fonts (HeiseiKakuGo-W5 / NotoSansJP) | Railway (in-process) |

### 1.2 Production URLs

| Environment | URL |
|---|---|
| Frontend (Production) | https://nextcareer.pro |
| Backend (Production) | https://naitei-backend-production.up.railway.app |

### 1.3 Key Design Decisions

- **No database**: All user state is held in `sessionStorage` (browser-only, per-tab). No server-side persistence.
- **SSE streaming**: All LLM text generation uses Server-Sent Events for real-time output display.
- **API proxy pattern**: Frontend never calls the FastAPI backend directly. All requests go through Next.js API Routes to avoid CORS issues and centralize auth/headers.
- **3-provider cascade**: AI requests attempt Claude first, then fall back to OpenAI, then Gemini.
- **All pages are client components**: Every `page.tsx` uses `'use client'` directive.

---

## 2. User Flow (4-Step Wizard)

```
Landing Page (/) 
    |
    v
Step 1: Job Posting Input (/step1)
    | saves CompanyInfo to sessionStorage('naitei_company')
    v
Step 2: Applicant Profile (/step2)
    | saves ApplicantProfile to sessionStorage('naitei_applicant')
    v
Step 3: Document Review (/step3)
    | reads both from sessionStorage, streams review via SSE
    v
Step 4: Interview Preparation (/step4)
    | reads both from sessionStorage, streams 4 panels via SSE
    v
Done Page (/done)
    | clear sessionStorage on restart
```

### 2.1 Step 1 - Job Posting Input (`/step1`)

Three input modes are available (selected via `ModeToggle` component):

| Mode | Description |
|---|---|
| `url` | User enters a job posting URL. Frontend calls `POST /api/scrape` which fetches and parses the page content using AI. Shows 3-step progress: fetch -> parse -> extract. |
| `file` | User uploads PDF/Word/image via `FileUploader` component (drag-and-drop). File is sent to backend for text extraction. |
| `text` | User pastes raw job posting text into a textarea (10,000 char limit). A "sample text" button fills demo content. |

**Output**: `CompanyInfo` object saved to `sessionStorage.setItem('naitei_company', JSON.stringify(data))`.

### 2.2 Step 2 - Applicant Profile (`/step2`)

Two input modes:

| Mode | Description |
|---|---|
| `file` | Upload resume file -> AI extraction via `POST /api/extract` -> auto-parses to `ApplicantProfile` struct |
| `manual` | Manual form entry: name (required), birthdate (auto-calculates age), address, career history entries (add/remove/reorder), qualifications, self-PR |

**Output**: `ApplicantProfile` object saved to `sessionStorage.setItem('naitei_applicant', JSON.stringify(data))`.

### 2.3 Step 3 - Document Review (`/step3`)

- Auto-starts SSE stream on mount via `apiClient.reviewStream()`
- Reads `CompanyInfo` + `ApplicantProfile` from sessionStorage
- Displays streaming progress: animated dot, elapsed time, progress messages
- Tab view: "Original" vs "Revised" with blinking cursor during stream
- PDF download button: calls `apiClient.exportPdf()` -> creates Blob -> triggers browser download
- Abort capability for long-running streams

### 2.4 Step 4 - Interview Preparation (`/step4`)

Four independent streaming tabs, each with its own `StreamingPanel`:

| Tab Key | Endpoint | Content |
|---|---|---|
| `qa` | `POST /api/interview/qa` | Predicted Q&A pairs organized by category (8 categories) |
| `pr` | `POST /api/interview/pr` | Self-PR scripts in 3 lengths: 60s, 90s, 3min |
| `questions` | `POST /api/interview/questions` | Reverse questions for the applicant to ask |
| `checklist` | `POST /api/interview/checklist` | Pre-interview preparation checklist by phase |

Each tab supports:
- Keyword search filter
- Favorites (star toggle)
- Text-to-speech (Web Speech API)
- Regenerate button
- Bulk PDF download as ZIP

### 2.5 Done Page (`/done`)

- Gradient background with animated checkmark
- 4-item completion checklist
- Restart button clears sessionStorage and redirects to `/`

---

## 3. State Management

### 3.1 sessionStorage Keys

| Key | Type | Written By | Read By |
|---|---|---|---|
| `naitei_company` | `CompanyInfo` (JSON) | Step 1 | Step 3, Step 4 |
| `naitei_applicant` | `ApplicantProfile` (JSON) | Step 2 | Step 3, Step 4 |

No other persistence mechanism is used. Closing the browser tab loses all data.

### 3.2 Domain Types

#### `CompanyInfo` (`types/applicant.ts`)

```typescript
interface CompanyInfo {
  readonly name: string;
  readonly url?: string;
  readonly jobTitle: string;
  readonly jobDescription: string;
  readonly requirements: readonly string[];
  readonly preferredSkills: readonly string[];
  readonly employmentType?: string;
  readonly salary?: string;
  readonly selectionFlow: readonly string[];
  readonly rawText: string;
}
```

#### `ApplicantProfile` (`types/applicant.ts`)

```typescript
interface ApplicantProfile {
  readonly name: string;
  readonly age?: number;
  readonly email?: string;
  readonly phone?: string;
  readonly address?: string;
  readonly careerHistory: readonly CareerItem[];
  readonly qualifications: readonly string[];
  readonly selfPr?: string;
  readonly rawText: string;
}

interface CareerItem {
  readonly company: string;
  readonly periodFrom: string;        // YYYY-MM
  readonly periodTo: string | null;   // null = currently employed
  readonly role: string;
  readonly achievements: readonly string[];
}
```

### 3.3 Wizard Step Definitions (`types/wizard.ts`)

```typescript
type StepKey = 'job' | 'profile' | 'review' | 'interview';

const STEPS = [
  { key: 'job',       label: '募集要項入力', path: '/step1', stepNumber: 1 },
  { key: 'profile',   label: '応募者情報',   path: '/step2', stepNumber: 2 },
  { key: 'review',    label: '書類添削',     path: '/step3', stepNumber: 3 },
  { key: 'interview', label: '面接対策',     path: '/step4', stepNumber: 4 },
];

type Step1Mode = 'url' | 'file' | 'text';
type Step2Mode = 'file' | 'manual';
type SaveStatus = 'saved' | 'saving' | 'error' | 'unsaved';
```

---

## 4. API Layer

### 4.1 Proxy Architecture

All frontend requests go through Next.js API Routes, which proxy to the FastAPI backend:

```
Browser -> fetch('/api/review', ...) 
    -> Next.js API Route (app/api/review/route.ts)
        -> fetch(BACKEND_URL + '/api/review', ...) 
            -> FastAPI endpoint
```

The proxy layer (`lib/backend.ts`) provides:

```typescript
const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

function backendUrl(path: string): string;    // builds full backend URL
function proxySSE(upstreamRes: Response): ReadableStream<Uint8Array>;  // passthrough SSE
const SSE_HEADERS = { 'Content-Type': 'text/event-stream', ... };
```

### 4.2 Frontend API Client (`lib/api-client.ts`)

Unified client used by page components:

```typescript
const apiClient = {
  scrape(url, opts?) -> Promise<ApiResponse<ScrapeResponse>>,
  extract(file, kind?) -> Promise<ApiResponse<ExtractResponse>>,
  reviewStream(req, signal?) -> AsyncIterable<string>,
  interviewStream(type, req, signal?) -> AsyncIterable<string>,
  chatStream(req, signal?) -> AsyncIterable<string>,
  researchStream(company, signal?) -> AsyncIterable<string>,
  exportPdf(req) -> Promise<Blob>,
};
```

SSE parsing logic:
- `event: content` + `data: {"delta":"..."}` -> yields delta string
- `event: done` -> terminates iteration
- `event: error` + `data: {"message":"..."}` -> throws Error

### 4.3 API Response Envelope (`types/api.ts`)

```typescript
interface ApiSuccess<T> {
  readonly success: true;
  readonly data: T;
  readonly error: null;
  readonly meta?: ApiMeta;
}

interface ApiFailure {
  readonly success: false;
  readonly data: null;
  readonly error: ApiError;
  readonly meta?: ApiMeta;
}

interface ApiMeta {
  readonly requestId: string;
  readonly latencyMs?: number;
  readonly usage?: { promptTokens, completionTokens, totalTokens, costUsd? };
  readonly model?: string;
  readonly provider?: 'claude' | 'openai' | 'gemini';
}

interface ApiError {
  readonly code: ErrorCode;
  readonly message: string;
  readonly details?: Record<string, unknown>;
  readonly retryable: boolean;
}
```

### 4.4 Error Codes (enum ErrorCode)

| Code | Category |
|---|---|
| `BAD_REQUEST`, `VALIDATION_FAILED`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND` | 4xx Client |
| `PAYLOAD_TOO_LARGE`, `UNSUPPORTED_MIME`, `FILE_TOO_LARGE`, `FILE_SIGNATURE_MISMATCH` | File validation |
| `INVALID_URL`, `SSRF_BLOCKED`, `RATE_LIMITED` | Security |
| `INTERNAL_ERROR`, `AI_PROVIDER_ERROR`, `AI_TIMEOUT`, `AI_QUOTA_EXCEEDED`, `AI_CONTENT_FILTERED` | AI/Server |
| `SCRAPE_FAILED`, `SCRAPE_TIMEOUT`, `PDF_RENDER_FAILED`, `EXTERNAL_DEPENDENCY` | External |

---

## 5. Backend Endpoints (FastAPI - `main.py`, 1,227 lines)

All endpoints are prefixed with `/api/`.

### 5.1 GET /api/health

Health check. Returns `{"status": "ok"}`.

### 5.2 POST /api/scrape

Fetches a job posting URL, extracts text, and structures the content using AI.

- **Request**: `ScrapeRequest { url, waitForSelector?, timeoutMs?, ai? }`
- **Response**: `ApiResponse<ScrapeResponse>` with structured fields (companyName, jobTitle, requirements, etc.)
- **Security**: SSRF protection validates HTTPS-only, resolves DNS, checks against private IP ranges
- **Rate limit**: 10 requests / 600 seconds per IP

### 5.3 POST /api/extract

Extracts applicant profile from uploaded file (PDF, DOCX, image).

- **Request**: `multipart/form-data` with `file` field + optional `kind` field
- **Response**: `ApiResponse<ExtractResponse>` with `ApplicantProfile` + source metadata
- **File validation**: Magic byte checking (PDF: `%PDF`, PNG: `\x89PNG`, JPEG: `\xFF\xD8\xFF`), 10MB max
- **Text extraction**: DOCX via python-docx, PDF via PyPDF2, images via AI vision

### 5.4 POST /api/review (SSE)

AI-powered document review and correction.

- **Request**: `ReviewRequest { applicant, company, target, tone?, ai? }`
- **Response**: SSE stream (`event: content` / `event: done` / `event: error`)
- **Output**: Markdown-formatted review with original vs revised sections, diffs, comments, scores

### 5.5 POST /api/interview/qa (SSE)

Generates predicted interview Q&A pairs.

- **Request**: `InterviewQaRequest { applicant, company, interviewer?, phase, minQuestions?, riskTopics? }`
- **Response**: SSE stream of Markdown with categorized questions (8 categories: intro, motivation, career, job, culture, risk, character, closing)

### 5.6 POST /api/interview/pr (SSE)

Generates self-PR scripts.

- **Request**: `InterviewPrRequest { applicant, company, emphasis?, tone?, ai? }`
- **Response**: SSE stream with 3 script variants (60-second, 90-second, 3-minute), design notes, NG phrases

### 5.7 POST /api/interview/questions (SSE)

Generates reverse questions (questions the applicant should ask).

- **Request**: `InterviewQuestionsRequest { applicant, company, interviewer?, phase, minQuestions? }`
- **Response**: SSE stream with categorized questions (business, enthusiasm, org, longterm), intents, NG examples, strategy

### 5.8 POST /api/interview/checklist (SSE)

Generates pre-interview preparation checklist.

- **Request**: `InterviewChecklistRequest { applicant, company, interviewDate, interviewLocation?, ai? }`
- **Response**: SSE stream with phased checklist (three_days_before, day_before, morning, arrival_to_exit, after, waiting, emergency)

### 5.9 POST /api/interview/chat (SSE)

Chat-based interview coaching with context from all generated materials.

- **Request**: `ChatRequest { sessionId, context: { jobInfo, userProfile, interviewMaterials }, messages, newMessage, ai? }`
- **Response**: SSE stream with conversational AI response

### 5.10 POST /api/research (SSE)

Company research across multiple dimensions.

- **Request**: `ResearchRequest { company, scope: ('company'|'industry'|'role'|'selection'|'interviewer')[], interviewerHint?, maxSources?, ai? }`
- **Response**: SSE stream with research sections, highlights, and source citations

### 5.11 POST /api/pdf

Generates PDF documents from interview materials.

- **Request**: `InterviewPdfRequest { materials: { qa?, pr?, questions?, checklist? }, applicantName, companyName, jobTitle }`
- **Response**: Binary PDF (single file) or ZIP (multiple files)
- **PDF engine**: ReportLab with Japanese font support (HeiseiKakuGo-W5 primary, NotoSansJP TTF fallback, background download as last resort)
- **Content type**: `application/pdf` or `application/zip`

---

## 6. AI Provider System

### 6.1 Provider Implementations (Backend - `main.py`)

Three provider classes, all supporting SSE streaming:

| Provider | SDK | Model |
|---|---|---|
| `ClaudeProvider` | `AsyncAnthropic` (anthropic SDK) | claude-haiku-4-5 |
| `OpenAIProvider` | `httpx` (direct HTTP) | gpt-4o |
| `GeminiProvider` | `httpx` (direct HTTP) | gemini-2.5-flash |

### 6.2 Cascade Fallback

```
Claude -> OpenAI -> Gemini
```

If the primary provider fails (timeout, quota, error), the system automatically tries the next provider. This is implemented in the backend's `sse_stream()` helper.

### 6.3 MODEL_MAP (Backend)

All task types use the same model per provider:

| Provider | Model ID |
|---|---|
| Claude | claude-haiku-4-5 |
| OpenAI | gpt-4o |
| Gemini | gemini-2.5-flash |

### 6.4 SSE Stream Format

Backend emits:

```
event: content
data: {"delta": "...text chunk..."}

event: content
data: {"delta": "...more text..."}

event: done
data: {}
```

On error:

```
event: error
data: {"message": "error description"}
```

### 6.5 Frontend AI Factory (`lib/ai/factory.ts`)

The frontend also has an AI provider abstraction using Vercel AI SDK v6 for potential direct-to-provider calls (currently unused in production flow, which uses the proxy):

```typescript
type TaskKind = 'extract_job_posting' | 'extract_resume' | 'review_document' |
  'generate_qa' | 'generate_pr' | 'generate_questions' | 'generate_checklist' |
  'research_company' | 'chat';

type AIProviderName = 'claude' | 'openai' | 'gemini';
```

Dependencies: `@ai-sdk/anthropic`, `@ai-sdk/openai`, `@ai-sdk/google`

### 6.6 PII Masking

The backend applies PII masking to all SSE output using regex patterns:
- Email addresses
- Phone numbers
- Postal codes
- Birthdays
- Japanese names (partial)

---

## 7. Frontend Component Architecture

### 7.1 Page Components

| Path | File | Description |
|---|---|---|
| `/` | `app/page.tsx` | Landing page: hero, 4-step explanation, 3 benefits, testimonials, FAQ accordion, CTA, footer |
| `/step1` | `app/step1/page.tsx` | Job posting input (3 modes: URL/file/text) |
| `/step2` | `app/step2/page.tsx` | Applicant profile (2 modes: file/manual) |
| `/step3` | `app/step3/page.tsx` | Document review (SSE streaming, tab view, PDF download) |
| `/step4` | `app/step4/page.tsx` | Interview prep (4 independent streaming panels) |
| `/done` | `app/done/page.tsx` | Completion page (animated checkmark, checklist, restart) |

### 7.2 Layout Components (`components/layout/`)

| Component | Description |
|---|---|
| `AppHeader.tsx` | Sticky header with logo "NextCareer", StepIndicator (wizard pages), SaveStatusBadge, help button. Navy background (`--color-primary-900`). |
| `WizardFooter.tsx` | Sticky bottom footer with Back/Next buttons, loading state, disabled reason tooltip, safe area inset for mobile. |
| `SaveStatusBadge.tsx` | Auto-save status indicator: saved/saving/error/unsaved with icons and relative time. |

### 7.3 Wizard Components (`components/wizard/`)

| Component | Description |
|---|---|
| `StepIndicator.tsx` | 4-step progress: completed (checkmark), current (highlighted ring), future (gray). Connector lines. Compact/full variants. Optional click-to-jump. |
| `ModeToggle.tsx` | Generic radio group toggle with keyboard nav (arrow keys), ARIA radiogroup, sizes sm/md/lg, fullWidth option. |

### 7.4 Upload Components (`components/upload/`)

| Component | Description |
|---|---|
| `FileUploader.tsx` | Drag-and-drop uploader. Props: accept (MIME types), maxSizeMb, multiple, onFiles, cameraCapture. Features: drag-over animation, file validation (size + MIME), simulated progress bar, camera capture input, error display, uploaded file list with remove. |

### 7.5 UI Components (`components/ui/`)

shadcn/ui primitives: `badge`, `button`, `card`, `input`, `label`, `progress`, `scroll-area`, `separator`, `tabs`, `textarea`.

### 7.6 Custom Hooks (`hooks/`)

| Hook | Description |
|---|---|
| `useReducedMotion.ts` | Monitors `prefers-reduced-motion` media query. Returns boolean. Used to disable Framer Motion animations for accessibility. |
| `useSaveStatus.ts` | Debounced auto-save state management. Returns `{ status, markSaving, markSaved, markError }`. |

### 7.7 Utility Functions (`lib/`)

| File | Description |
|---|---|
| `api-client.ts` | Unified API client (see Section 4.2) |
| `backend.ts` | Backend proxy helper (see Section 4.1) |
| `cn.ts` | Tailwind class merge utility (`clsx` + `twMerge`) |
| `utils.ts` | General utilities |

---

## 8. Design System

### 8.1 Color System (OKLCH)

Defined in `app/globals.css` as CSS custom properties:

**Primary Palette ("Trust Navy")**:
- `--color-primary-50` through `--color-primary-900` (10 shades)

**Secondary Palette**:
- `--color-secondary-50` through `--color-secondary-700`

**Accent**:
- `--color-accent-400`, `--color-accent-500`

**Semantic Colors**:
- `--color-success`, `--color-warning`, `--color-error`, `--color-info`

**Surface System**:
- `--color-bg`, `--color-surface`, `--color-surface-2`, `--color-border`, `--color-text`, `--color-text-muted`

**shadcn/ui Integration**: Standard CSS variables (`--background`, `--foreground`, `--card`, `--primary`, etc.) are mapped to the OKLCH palette for seamless component styling.

### 8.2 Typography Scale

Responsive sizing with `clamp()`:

| Token | Range |
|---|---|
| `--text-display` | Display headings |
| `--text-hero` | Hero section text |
| `--text-h1` through `--text-h4` | Heading hierarchy |
| `--text-body` | Body text |
| `--text-small` | Small text |
| `--text-caption` | Captions |

Font: Noto Sans JP (loaded via `next/font/google`).

### 8.3 Spacing & Shadows

- `--space-section-y`: Section vertical padding
- `--space-card-pad`: Card internal padding
- `--shadow-card`: Card elevation shadow
- `--shadow-pop`: Pop-up/modal shadow

### 8.4 Dark Mode

Full dark mode theme variant defined in `globals.css` under `.dark` class, remapping all surface, text, and semantic color tokens.

### 8.5 Motion

- **Library**: Framer Motion (`framer-motion@12.38.0`)
- **Patterns**: `AnimatePresence` for page transitions, `motion.div` for card animations
- **Accessibility**: `useReducedMotion` hook disables all motion when OS preference is set
- **CSS**: `@media (prefers-reduced-motion: reduce)` override in `globals.css`

### 8.6 Tailwind Integration (`tailwind.config.ts`)

All CSS custom properties are mapped to Tailwind utility classes:
- Colors: `bg-primary-500`, `text-secondary-200`, etc.
- Typography: `text-display`, `text-hero`, etc.
- Spacing: `py-section-y`, `p-card-pad`, etc.
- Shadows: `shadow-card`, `shadow-pop`
- Border radius: Mapped from CSS variables

---

## 9. Security

### 9.1 CSP (Content Security Policy)

Per-request nonce-based CSP header set via FastAPI middleware:

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'nonce-{RANDOM}';
  ...
```

### 9.2 HTTP Security Headers

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
```

### 9.3 Rate Limiting

Token bucket algorithm per IP per endpoint prefix:

| Endpoint Prefix | Limit |
|---|---|
| `/api/scrape` | 10 requests / 600 seconds |
| Other endpoints | Configured per prefix |

### 9.4 SSRF Protection

Applied to `/api/scrape` URL validation:
- HTTPS-only (rejects HTTP)
- DNS resolution check
- Blocks private IP ranges (10.x, 172.16-31.x, 192.168.x, 127.x, ::1)

### 9.5 File Validation

- Magic byte verification: PDF (`%PDF`), PNG (`\x89PNG`), JPEG (`\xFF\xD8\xFF`)
- Maximum file size: 10MB
- MIME type whitelist

### 9.6 PII Masking

Regex-based masking applied to all SSE output:
- Email addresses
- Phone numbers (Japanese format)
- Postal codes
- Birthdates
- Japanese names (partial masking)

### 9.7 Request Tracking

- Unique request ID generated per request (`X-Request-ID` header)
- Response timing tracked (`X-Response-Time` header)

---

## 10. API Routes (Next.js Proxy Layer)

Each route file in `webapp/app/api/` proxies requests to the FastAPI backend:

| Route File | Method | Backend Path | Type |
|---|---|---|---|
| `api/health/route.ts` | GET | `/api/health` | JSON |
| `api/scrape/route.ts` | POST | `/api/scrape` | JSON |
| `api/extract/route.ts` | POST | `/api/extract` | FormData -> JSON |
| `api/review/route.ts` | POST | `/api/review` | SSE passthrough |
| `api/interview/qa/route.ts` | POST | `/api/interview/qa` | SSE passthrough |
| `api/interview/pr/route.ts` | POST | `/api/interview/pr` | SSE passthrough |
| `api/interview/questions/route.ts` | POST | `/api/interview/questions` | SSE passthrough |
| `api/interview/checklist/route.ts` | POST | `/api/interview/checklist` | SSE passthrough |
| `api/interview/chat/route.ts` | POST | `/api/interview/chat` | SSE passthrough |
| `api/research/route.ts` | POST | `/api/research` | SSE passthrough |
| `api/pdf/route.ts` | POST | `/api/pdf` | Binary passthrough |

SSE routes use `proxySSE()` to pass through the upstream `ReadableStream<Uint8Array>` with `SSE_HEADERS`.

---

## 11. Backend Internals (`main.py`)

### 11.1 Pydantic Models

All models inherit from `CamelModel` which provides automatic camelCase alias generation for JSON serialization:

```python
class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
```

Key models: `ApplicantProfile`, `CompanyInfo`, `SessionState`, `InterviewMaterials`, plus all request/response models.

### 11.2 Japanese Font Initialization

Three-level fallback for PDF font support:
1. `HeiseiKakuGo-W5` (built-in ReportLab CID font)
2. `NotoSansJP` TTF (local file)
3. Background download of NotoSansJP from Google Fonts API

### 11.3 Text Extraction

`extract_text_from_file()` handles:
- **DOCX**: Via `python-docx` library, extracts paragraph text
- **PDF**: Via `PyPDF2`, extracts text from all pages
- **Plain text**: Direct UTF-8 decode

### 11.4 PDF Generation

`_markdown_to_pdf_bytes()` using ReportLab:
- Parses markdown headings (`#`, `##`, `###`) into styled paragraphs
- Japanese font rendering
- Returns `bytes` for single PDF or ZIP for multiple documents

### 11.5 Security Middleware Stack

Applied as FastAPI middleware in order:
1. Request ID assignment
2. CSP nonce generation
3. Security headers (HSTS, X-Frame-Options, etc.)
4. Rate limiting (token bucket)
5. Response timing

---

## 12. Environment Variables

### 12.1 Frontend (Vercel)

| Variable | Purpose |
|---|---|
| `BACKEND_URL` | FastAPI backend URL (server-side, used by API routes) |
| `NEXT_PUBLIC_BACKEND_URL` | Backend URL (client-side fallback, typically empty in production) |

### 12.2 Backend (Railway)

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `GOOGLE_API_KEY` | Gemini API key |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) |

---

## 13. Testing

### 13.1 Unit Tests

- **Framework**: Vitest (`vitest@4.1.5`)
- **Location**: `components/__tests__/`, `lib/__tests__/`
- **Run**: `npm run test` (single run), `npm run test:watch` (watch mode)
- **Coverage target**: 80%+

### 13.2 E2E Tests

- **Framework**: Playwright (`@playwright/test@1.59.1`)
- **Location**: `e2e/golden-path.spec.ts`
- **Run**: `npm run test:e2e`
- **Scope**: Full wizard flow (30 tests, all passing)

### 13.3 Backend Tests

- **Framework**: pytest
- **Location**: `test_main.py`
- **Run**: `pytest test_main.py -v`

---

## 14. CI/CD Pipeline

**Config**: `.github/workflows/ci.yml`

Pipeline stages:
1. `unit-test` - Run Vitest unit tests
2. `e2e-test` - Run Playwright E2E tests
3. `deploy` - Deploy to Vercel (on main branch merge)

**Note**: Jobs use repository root as working directory (no explicit `working-directory` setting).

---

## 15. Dependencies

### 15.1 Frontend Key Packages

| Package | Version | Purpose |
|---|---|---|
| `next` | 14.2.35 | React framework |
| `react` / `react-dom` | 18.x | UI library |
| `typescript` | 5.x | Type system |
| `ai` | 6.0.169 | Vercel AI SDK |
| `@ai-sdk/anthropic` | 3.0.72 | Claude provider |
| `@ai-sdk/openai` | 3.0.54 | OpenAI provider |
| `@ai-sdk/google` | 3.0.65 | Gemini provider |
| `framer-motion` | 12.38.0 | Animation |
| `lucide-react` | 1.14.0 | Icons (unified) |
| `tailwind-merge` | 3.5.0 | Class merging |
| `react-hook-form` | 7.74.0 | Form handling |
| `react-dropzone` | 15.0.0 | File upload |
| `zod` | 4.3.6 | Schema validation |
| `zustand` | 5.0.12 | Client state |
| `@tanstack/react-query` | 5.100.6 | Server state |
| `vitest` | 4.1.5 | Unit testing |
| `@playwright/test` | 1.59.1 | E2E testing |

### 15.2 Backend Key Packages

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `anthropic` | Claude SDK (AsyncAnthropic) |
| `httpx` | HTTP client (OpenAI/Gemini direct) |
| `pydantic` | Data validation (v2) |
| `python-docx` | DOCX text extraction |
| `PyPDF2` | PDF text extraction |
| `reportlab` | PDF generation |
| `python-multipart` | File upload handling |

---

## 16. Directory Structure

```
Next_Career 2/
├── main.py                          # FastAPI backend (1,227 lines)
├── test_main.py                     # Backend tests
├── requirements.txt                 # Python dependencies
├── CLAUDE.md                        # Project instructions
├── .github/workflows/ci.yml         # CI/CD pipeline
├── webapp/                          # Next.js frontend
│   ├── app/
│   │   ├── layout.tsx               # Root layout (Noto Sans JP, skip link)
│   │   ├── page.tsx                 # Landing page
│   │   ├── globals.css              # Design tokens (OKLCH system)
│   │   ├── step1/page.tsx           # Job posting input
│   │   ├── step2/page.tsx           # Applicant profile
│   │   ├── step3/page.tsx           # Document review
│   │   ├── step4/page.tsx           # Interview preparation
│   │   ├── done/page.tsx            # Completion page
│   │   └── api/                     # Next.js API Routes (proxy)
│   │       ├── health/route.ts
│   │       ├── scrape/route.ts
│   │       ├── extract/route.ts
│   │       ├── review/route.ts
│   │       ├── pdf/route.ts
│   │       ├── research/route.ts
│   │       └── interview/
│   │           ├── qa/route.ts
│   │           ├── pr/route.ts
│   │           ├── questions/route.ts
│   │           ├── checklist/route.ts
│   │           └── chat/route.ts
│   ├── components/
│   │   ├── layout/                  # AppHeader, WizardFooter, SaveStatusBadge
│   │   ├── wizard/                  # StepIndicator, ModeToggle
│   │   ├── upload/                  # FileUploader
│   │   └── ui/                      # shadcn/ui primitives
│   ├── hooks/                       # useReducedMotion, useSaveStatus
│   ├── lib/
│   │   ├── api-client.ts            # Unified API client
│   │   ├── backend.ts               # Backend proxy helper
│   │   ├── ai/factory.ts            # AI provider factory
│   │   ├── cn.ts                    # Tailwind class merge
│   │   └── utils.ts                 # General utilities
│   ├── types/
│   │   ├── applicant.ts             # CompanyInfo, ApplicantProfile, CareerItem
│   │   ├── api.ts                   # API request/response types, ErrorCode enum
│   │   ├── ai.ts                    # AIProviderName, TaskKind, AIUsage, AIStreamChunk
│   │   └── wizard.ts               # StepKey, STEPS, Step1Mode, Step2Mode, SaveStatus
│   ├── e2e/
│   │   └── golden-path.spec.ts      # Playwright E2E tests (30 tests)
│   ├── package.json
│   ├── tailwind.config.ts           # Tailwind custom theme mapping
│   ├── tsconfig.json
│   └── next.config.mjs
├── 応募者情報/                       # Applicant profile documents (input)
└── 応募対象会社/                     # Target company folders (input/output)
    └── <company>/
        ├── 募集情報/                 # Job posting PDFs
        ├── 調査結果/                 # Research output
        └── 面接対策/<NN>_<interview>/
            ├── 01_想定問答集.md
            ├── 02_自己PR案.md
            ├── 03_逆質問集.md
            ├── 04_事前準備チェックリスト.md
            └── スライド/
```

---

## 17. Data Flow Diagrams

### 17.1 Step 1 (URL Mode)

```
User enters URL
    -> POST /api/scrape { url }
    -> Next.js API Route proxies to FastAPI
    -> FastAPI: SSRF check -> fetch URL -> extract text -> AI structuring
    -> Response: { structured: { companyName, jobTitle, requirements, ... } }
    -> Frontend maps to CompanyInfo
    -> sessionStorage.setItem('naitei_company', JSON.stringify(companyInfo))
```

### 17.2 Step 3 (Review Stream)

```
Page mounts, reads sessionStorage
    -> POST /api/review { applicant, company, target: 'both' }
    -> Next.js API Route: proxySSE(upstreamRes)
    -> FastAPI: build prompt -> ClaudeProvider.stream() -> SSE events
    -> Frontend: for await (const delta of apiClient.reviewStream(req))
       -> append delta to displayed text
       -> update progress indicators
    -> On 'done': show complete review with tabs (original/revised)
```

### 17.3 Step 4 (Interview Panels)

```
Each tab independently:
    -> POST /api/interview/{qa|pr|questions|checklist}
    -> SSE stream -> StreamingPanel component
    -> Features: search, favorites, TTS, regenerate
    -> "Download All" -> POST /api/pdf -> ZIP blob -> browser download
```

---

## 18. Known Constraints & Limitations

1. **No persistence**: All data is lost when the browser tab closes (sessionStorage only)
2. **Single-user**: No authentication, no user accounts, no multi-session support
3. **Japanese-only**: UI text, prompts, and font support are Japanese-specific
4. **AI cost**: Each generation consumes API tokens; no caching of LLM responses
5. **File size**: Maximum 10MB upload per file
6. **No websocket**: Uses SSE (unidirectional); chat is request-response over SSE, not bidirectional websocket
7. **PDF fonts**: Japanese font availability depends on server environment (3-level fallback)
