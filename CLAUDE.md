# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 📈 プロジェクト進捗状況（2026/5/3 時点）

### ✅ 完了した作業

| タスク | 状態 | 備考 |
|---|---|---|
| バックエンド（main.py） | ✅ 完了 | FastAPI 35KB、全37テスト パス |
| 設計フェーズ全体 | ✅ 完了 | PRD / システム設計 / API設計 / UI設計 / AI連携設計 |
| フロントエンド実装 | ✅ 完了 | Next.js 14 App Router、5ステップウィザード完成 |
| 単体テスト・統合テスト | ✅ 完了 | Vitest、テストカバレッジ 80%+ |
| E2E テストフレームワーク | ✅ 完了 | Playwright golden-path test 実装 |
| GitHub Actions CI/CD | ✅ 完了 | ✅ 2026/5/3 修正：`working-directory: webapp` 削除済み |

### 🔄 進行中・検証待ち

| タスク | 状態 | 次ステップ |
|---|---|---|
| **E2E テスト 24 個失敗** | ✅ **解決済み** | 全30テスト合格（2026/5/4 11:30） |
| GitHub Actions ワークフロー検証 | 🔄 進行中 | unit-test → e2e-test → deploy ジョブの実行確認 |
| Vercel デプロイ | ⚠️ 検証待ち | 404 DEPLOYMENT_NOT_FOUND エラーの原因調査・解決 |
| バックエンド接続確認 | ⚠️ 検証待ち | フロント → Railway バックエンド通信テスト |
| 本番環境 E2E フロー | ⚠️ 検証待ち | Step1 → Step4 → PDF 出力の全体フロー検証 |

### 【詳細】E2E テスト 24 個失敗の根本原因診断フレームワーク（2026/5/4）

## 【解決】実際の根本原因と修正（2026/5/4 完了）

**根本原因**: ビルドプロセスが実行されていなかった

**修正手順**:
1. `npm run build` を実行 → Tailwind CSS クラス生成が発動
2. `npm run test:e2e` を実行 → 全30テスト合格

**解説**:
- Tailwind CSS クラスは `npm run dev` 時には On-Demand で生成される（ホットリロード対応）
- 本番環境では `npm run build` で静的なクラスファイルを生成する必要
- E2E テストは本番ビルド（`npm run build`）後の状態をテストするため、ビルドプロセスが必須
- 前セッションでは設定ファイルの検証に集中していたが、実は配置は完全に正常だった
- **学び**: 次回以降は「コードは正しいのか？」ではなく「プロセスは実行されているか？」を優先的に確認すべき

## 【最新判定】2026/5/4 診断フェーズ2完了

### 4仮説の検証結果

| # | 仮説 | 検証対象 | 結果 | 根拠 |
|---|---|---|---|---|
| ① | useReducedMotion SSR互換性 | `hooks/useReducedMotion.ts` | ✅ NOT | 'use client' 指定、useEffect 内で window アクセス |
| ② | STEPS const as const | `types/wizard.ts` | ✅ NOT | as const アサーション正常、型推論チェーン正常 |
| ③ | CSS変数未定義 | `app/globals.css` | ✅ 修正 | 変数は定義済み、但しビルドプロセス検証が必要 |
| ④ | AppHeader Props未処理 | `components/layout/AppHeader.tsx` | ✅ NOT | Props型定義・値渡し正常 |

### 新仮説：Tailwind 設定 / ビルドプロセス

根本原因は以下のいずれかの可能性：
1. `tailwind.config.ts` の `content` パスが Next.js App Router に対応していない
2. CSS 変数がビルド時にストリップされている
3. Tailwind が CSS 変数参照を正しく変換していない

### 次セッション即座アクション

```bash
# 1. tailwind.config.ts を確認
cat webapp/tailwind.config.ts | grep -A 10 "content:"

# 2. 本番ビルド
cd webapp && npm run build

# 3. E2E テスト再実行
npm run test:e2e

# 4. ブラウザで手動確認
npm run dev
# http://localhost:3000/step1 で h1 要素が DOM に存在するか確認


## 全体サマリ

**診断状況**
- 4つの初期仮説すべてを検証完了
- 3つは明確に根本原因を除外
- 1つ（CSS 変数）は変数定義自体は正常であることを確認
- ただし 24 E2E テスト失敗の根本原因は依然未特定

**判明した事実**
- ソースコードレベルでの実装エラーはなし
- CSS 変数は `app/globals.css` に正しく定義されている
- 相対パス解決（`app/layout.tsx` → `./globals.css` → `app/globals.css`）は正常
- useReducedMotion, STEPS const, AppHeader Props はすべて正常実装

**次のステップへの移行条件**
ビルドプロセスおよび Tailwind CSS 設定の検証が必須。本番ビルド（`npm run build`）と E2E テスト再実行（`npm run test:e2e`）で、エラーパターンまたは成功状況を確認することで、根本原因の特定が進展する。


### 🏗️ 最新の修正履歴

**GitHub Actions CI/CD 修正（2026/5/3）**
- **問題**：e2e-test ジョブが `working-directory: webapp` の指定で npm パッケージを見つけられない
- **原因**：GitHub Actions リポジトリ checkout 時に webapp ディレクトリがルートになっており、ネストされたパスが存在しない
- **解決**：`.github/workflows/ci.yml` の以下を修正
  - e2e-test ジョブ内の `working-directory: webapp` 4ヶ所を削除
  - artifact path を `path: webapp/playwright-report/` → `path: playwright-report/` に修正
- **ステータス**：コミット済み & リモートプッシュ完了

---

## 🎯 今後の検証予定

### Phase 1: CI/CD パイプライン検証（本週中）
```
実行: unit-test ジョブ
  → npm ci / tsc --noEmit / lint / test / build 成功確認
  ↓
実行: e2e-test ジョブ（unit-test 成功後）
  → Playwright browser install / build / e2e test 実行
  ↓
確認: Playwright Report アーティファクト生成
  ↓
実行: deploy ジョブ（両テスト成功後）
  → Vercel デプロイ開始
```

### Phase 2: Vercel デプロイ検証
- Vercel Dashboard でデプロイ状態確認（DEPLOYMENT_NOT_FOUND 原因調査）
- 環境変数確認：`NEXT_PUBLIC_API_URL` が正しく設定されているか
- ビルドログ確認：`Settings → Deployments` でエラーの有無

### Phase 3: 本番接続テスト
- バックエンド ヘルスチェック：`curl https://naitei-backend-production.up.railway.app/api/health`
- フロント → バック通信テスト：ステップ1 募集要項入力で /api/extract 呼び出し
- ストリーミング API テスト：ステップ4 面接対策で /api/interview/chat 呼び出し

### Phase 4: 完全フロー検証
- Step1 → Step2 → Step3 → Step4 → Done（PDF ダウンロード）の全フロー実行
- 各ステップでのエラーハンドリング動作確認
- E2E テスト `npm run test:e2e` が CI で成功することを確認

---

## 📐 コーディング規約・確定事項

### TypeScript / 型安全性
- **必須**: すべてのモジュール export は型定義付き
- **型定義の一元化**: `types/` ディレクトリに集約
  - `types/applicant.ts` — 応募者・求人・入力データ
  - `types/api.ts` — API リクエスト・レスポンス
  - `types/ai.ts` — AI モデル・ストリーミング型
- **import path**: 相対パスではなく `@/types`, `@/lib`, `@/components` 推奨
- **never use `any`**: `unknown` で受け取り、型ガード関数で narrowing

### React / コンポーネント設計
- **原則**: 機能単位のディレクトリ構成（ファイル種別ではなく）
- **小ぶり**: 1コンポーネント 200-400 行以下
- **Props 型定義**: インライン interface は避け、`types/` に集約
- **Hooks**: `useState` / `useCallback` / `useEffect` の使用は最小限
  - サーバー状態は **TanStack Query** で管理
  - クライアント状態は **Zustand** で管理
  - フォーム状態は **React Hook Form** で管理
- **memo 使用**: 不要な再レンダリング防止（`React.memo` 推奨）

### API / バックエンド連携
- **型安全**: すべての fetch は `Response.json() as <型>` で型チェック
- **エラーハンドリ**: 明示的な try-catch + ユーザー向けメッセージ表示
- **ストリーミング**: Vercel AI SDK の `streamText()` で実装
  - `toDataStreamResponse()` で Next.js との連携
  - フロント側は `useChat()` hook で受信

### テスト（80%+ 必須）
- **テスト先行**: RED → GREEN → REFACTOR の順序
- **単体テスト**（Vitest）: ロジック・util 関数・Hook
- **統合テスト**（Vitest）: API Routes / データフロー
- **E2E テスト**（Playwright）: ユーザー完全フロー（golden-path）
- **カバレッジ**: `npm run test --coverage` で 80% 以上を確認
- **テストファイル配置**:
  - コンポーネント: `components/__tests__/Component.test.tsx`
  - ロジック: `lib/__tests__/util.test.ts`
  - E2E: `e2e/golden-path.spec.ts`

### Git / コミット
- **コミットメッセージ**: 従来型（feat:, fix:, refactor:, test:, docs: など）
- **原則**: 1機能 = 1コミット
- **PR**: main へのマージ前に必ず `npm run test` で テスト全パス確認

### デプロイ前チェックリスト
- [ ] `npm run build` が成功（本番ビルド検証）
- [ ] `npm run test` で テストカバレッジ 80%+
- [ ] `npm run lint` で ESLint エラーなし
- [ ] 環境変数が `.env.example` に記載されているか
- [ ] GitHub Actions CI が全ステージ通過しているか
- [ ] Vercel デプロイが成功しているか（Preview URL 確認）

### CI/CD パイプライン設定
- **GitHub Actions ワークフロー**: `.github/workflows/ci.yml`
  - unit-test: Node 20, npm ci, type check, lint, test, build
  - e2e-test: Playwright browser install, build, run tests, artifact upload (failure時)
  - deploy: Vercel deployment (main branch push のみ)
- **注意**: 各 Job の `working-directory` は明示しない（リポジトリルートを使用）
- **Artifact**: Playwright report は 7 日保持

---

## 🚀 クイックスタート（開発者向け）

### よく使うコマンド

```bash
# フロントエンド開発
cd webapp
npm run dev                    # ローカル開発サーバー（http://localhost:3000）
npm run build && npm run start # 本番ビルド＆検証
npm run test                   # ユニットテスト（Vitest）
npm run test:watch             # テストをwatch modeで実行（推奨）
npm run test:e2e              # E2E テスト全実行（Playwright）
npm run lint                   # ESLint チェック

# バックエンド開発
pip install -r requirements.txt
uvicorn main:app --reload     # 開発サーバー（http://localhost:8000）
pytest test_main.py -v        # テスト全実行
pytest test_main.py::test_名前 -v  # 単一テスト実行
```

### 単一テスト実行（開発中推奨）

```bash
# 特定のテストファイル
npm run test -- --run src/lib/__tests__/ai-factory.test.ts

# 特定コンポーネントのテスト
npm run test -- --run components/FileUploader

# パターンマッチでテスト実行
npm run test -- --run api
```

### 本番環境チェック

| 環境 | URL | ダッシュボード |
|---|---|---|
| **Vercel（フロント）** | https://naitei-ai-webapp.vercel.app | [Vercel Dashboard](https://vercel.com/dashboard) |
| **Railway（バック）** | https://naitei-backend-production.up.railway.app | [Railway Dashboard](https://railway.app) |

**環境変数確認**
- Vercel: Settings → Environment Variables → `NEXT_PUBLIC_API_URL` を確認
- Railway: Project Settings → Variables → `OPENAI_API_KEY` など確認

---

## 📊 リポジトリ構成

このリポジトリは2つの独立した部分で構成される：

| パス | 役割 |
|---|---|
| `webapp/` | Next.js 14 フロントエンド（面接対策Webアプリ） |
| `main.py` | FastAPI バックエンド（PDF処理・AI連携・ZIP生成） |
| `process-docs/` | Webアプリ実装のためのプロセス仕様書（コードではない） |
| `応募者情報/`, `応募対象会社/` | 個人テストデータ（`.gitignore` 済み） |

---

## 🏗️ アーキテクチャ at a Glance

### フロントエンド（webapp/）

**フレームワーク**
- Next.js 14 (App Router) + TypeScript
- UI: shadcn/ui + Tailwind CSS + Framer Motion

**ルーティング構造**
- `app/page.tsx` → Step 1: 募集要項入力
- `app/step2/` → Step 2: 応募者情報
- `app/step3/` → Step 3: 書類添削
- `app/step4/` → Step 4: 面接対策
- `app/done/` → Step 5: PDF出力完了

**API Routes**（`app/api/` 配下）
- `health/` — ヘルスチェック（`GET /api/health`）
- `scrape/` → バックエンド `/api/scrape` にプロキシ
- `extract/` → バックエンド `/api/extract` にプロキシ
- `review/` → バックエンド `/api/review` にプロキシ
- `interview/chat/` → ストリーミング会話API
- `research/` → バックエンド `/api/research` にプロキシ
- `pdf/` → PDF生成・ダウンロード

**AI 連携（`lib/ai/factory.ts`）**
- Vercel AI SDK が Anthropic / OpenAI / Google を抽象化
- TaskKind ベースの MODEL_MAP で適切な LLM を選択
- ストリーミング対応（リアルタイム生成）

**状態管理**
- Zustand: クライアント状態（ウィザード進捗など）
- TanStack Query: サーバー状態（API レスポンス）

### バックエンド（main.py）

**フレームワーク**
- FastAPI 単一ファイル（35KB）

**主要エンドポイント**
- `POST /api/extract` — PDF から求人情報を抽出
- `POST /api/review` — 応募書類を添削
- `POST /api/interview/chat` — 面接練習（ストリーミング）
- `POST /api/research` — 業界・企業調査
- `POST /api/pdf` — 最終PDF生成（ZIP形式）
- `GET /api/health` — ヘルスチェック

**処理パイプライン**
```
PDF入力 → ReportLab で解析 → Claude API 呼び出し → 成果物生成
```

**デプロイ**
- Railway にデプロイ済み（`Procfile`, `railway.toml`）
- 本番URL: `https://naitei-backend-production.up.railway.app`

---

## ⚙️ コマンド（詳細）

### フロントエンド（webapp/）

```bash
cd webapp

# 開発
npm run dev          # ローカル開発サーバー（localhost:3000）

# ビルド・検証
npm run build        # 本番ビルド
npm run start        # ビルド済みアプリを起動

# テスト
npm run test         # ユニットテスト全実行（Vitest）
npm run test:watch   # テストをwatch modeで実行（推奨：開発中）
npm run test:e2e     # E2E テスト全実行（Playwright Chrome/Firefox/Safari）

# コード品質
npm run lint         # ESLint チェック

# パフォーマンス測定
npm run build && npm run start
# → http://localhost:3000 を Chrome DevTools Lighthouse で測定
```

### バックエンド（main.py）

```bash
# 依存関係インストール
pip install -r requirements.txt

# 開発サーバー起動
uvicorn main:app --reload

# テスト実行
pytest test_main.py -v

# 単一テスト実行（開発中推奨）
pytest test_main.py::test_extract_job_posting -v
pytest test_main.py::test_generate_pdf -v

# 全テスト＋カバレッジ
pytest test_main.py --cov=. --cov-report=term-missing
```

---

## 🔍 トラブルシューティング

### フロントエンド開発

#### E2E テストが失敗する
```
✗ Failed [chromium] › e2e/golden-path.spec.ts
```

**チェックリスト**
1. `NEXT_PUBLIC_API_URL` が `.env.local` に設定されているか確認
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
2. バックエンド（`main.py`）が起動しているか確認
   ```bash
   curl http://localhost:8000/api/health
   ```
3. 要素待機の失敗の場合 → `waitFor()` を明示的に使用
   ```ts
   await page.waitFor('button:has-text("Next")', { timeout: 5000 });
   ```

#### Lighthouse スコア低下
- **Performance < 90**
  - 画像最適化: `next/image` で `width`, `height` を明示
  - フォント: Preload は hero font のみ（`app/layout.tsx`）
  - CSS: Tailwind unused class → `tailwind.config.ts` の `content` 確認

- **Accessibility < 95**
  - ARIA ラベル確認: `aria-label`, `aria-describedby` 
  - キーボードナビゲーション: Tab キーで全要素を操作可能か確認

#### ビルドエラー
```
TypeError: Cannot read property 'NEXT_PUBLIC_API_URL'
```
→ `next build` 前に `.env.local` ファイルが存在することを確認

---

### バックエンド開発

#### API が 400/500 エラーを返す
```bash
# ローカルでテスト
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

**チェックリスト**
1. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` が `.env` に設定されているか確認
2. PDF ファイルが有効か確認（ReportLab で解析可能か）
3. バックエンドログを確認
   ```bash
   tail -f /tmp/uvicorn.log
   ```

#### テスト失敗時
```bash
# テスト単体で実行（キャッシュをリセット）
pytest test_main.py::test_extract_job_posting -v --cache-clear

# 詳細ログ出力
pytest test_main.py -v -s
```

---

### 本番環境（Vercel/Railway）

#### フロントエンドが 404
```
GET https://naitei-ai-webapp.vercel.app → 404 Not Found
```

**チェック**
1. Vercel Dashboard で最新デプロイが表示されているか確認
2. ビルドログにエラーがないか確認（Settings → Deployments）
3. 環境変数が正しく設定されているか確認

#### バックエンド接続失敗
```
Error: Failed to fetch https://naitei-backend-production.up.railway.app/api/extract
```

**チェック**
1. Railway Dashboard でアプリが「Running」状態か確認
2. ヘルスチェック実行
   ```bash
   curl https://naitei-backend-production.up.railway.app/api/health
   ```
3. 環境変数がすべて設定されているか確認（Railway → Project → Variables）

---

## 📚 参考：アーキテクチャ詳細

### フロントエンド構成

```
webapp/
├── app/
│   ├── layout.tsx              # 共通レイアウト（ナビゲーション）
│   ├── page.tsx                # Step 1 ページ
│   ├── step2/, step3/, step4/  # Step 2-4 ページ
│   ├── done/                   # 完了ページ
│   └── api/                    # API Routes（バックエンドプロキシ）
├── components/
│   ├── ui/                     # shadcn/ui コンポーネント
│   ├── StepIndicator.tsx       # ステップ進捗表示
│   ├── FileUploader.tsx        # PDF/ファイルアップロード
│   ├── StreamingText.tsx       # AIストリーミング表示
│   └── ReviewCard.tsx          # 添削結果カード
├── lib/
│   ├── ai/factory.ts           # AI プロバイダー抽象化
│   ├── backend.ts              # バックエンドAPI呼び出し
│   └── session.ts              # セッション管理
├── types/
│   ├── applicant.ts            # 応募者型定義
│   ├── api.ts                  # API レスポンス型
│   └── ai.ts                   # AI 関連型
└── styles/
    └── globals.css             # デザイントークン（OKLCH）
```

### テスト構成

```
webapp/
├── src/lib/__tests__/
│   ├── ai-factory.test.ts      # AI 選択ロジック
│   └── backend.test.ts         # API 通信
├── components/__tests__/
│   ├── StepIndicator.test.tsx  # コンポーネント
│   └── FileUploader.test.tsx
└── e2e/
    └── golden-path.spec.ts     # ユーザー完全フロー（Step1→PDF出力）
```

---

## 🎓 参考：開発パターン

### API 呼び出し（`lib/backend.ts`）

```ts
// ✅ 推奨：型安全な呼び出し
const response = await fetch('/api/extract', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(input)
});
const result = await response.json() as ExtractResponse;
```

### ストリーミング会話（`app/api/interview/chat/route.ts`）

```ts
// ✅ Vercel AI SDK でストリーミング対応
import { streamText } from 'ai';

const stream = await streamText({
  model: aiFactory.selectModel({ kind: 'interview' }),
  messages: [...],
  system: "You are a professional..."
});

return stream.toDataStreamResponse();
```

### テスト（Vitest + React Testing Library）

```ts
// ✅ ユーザー動作ベースのテスト
test('displays result after upload', async () => {
  render(<FileUploader />);
  const input = screen.getByRole('textbox');
  await userEvent.type(input, 'test.pdf');
  await userEvent.click(screen.getByRole('button', { name: /Upload/i }));
  await waitFor(() => {
    expect(screen.getByText(/Success/i)).toBeInTheDocument();
  });
});
```

---

# 転職支援システム（面接対策ワークフロー）【参照】

> 開発ガイドは上記のセクションを参照ください。以下は **面接対策ワークフロー** の完全リファレンスです。

このリポジトリは、応募者ごとに「応募者プロファイル × 応募先情報 × 面接官情報」を突き合わせて、**採用確率を最大化する面接対策成果物を自動生成する** 汎用ワークフローです。

---

## 🎯 このワークフローの目的

- 応募先ごとに **再現可能な調査・準備プロセス** を回す
- 面接1回ずつに対して **最高品質の成果物**（調査3ファイル＋対策4MD＋スライドPDF4ファイル）を生成する
- 応募者固有の職歴・資格・リスク質問を先回りして対策する
- 他応募案件でも同じ型で再利用できる

---

## 📁 ディレクトリ構造（標準型）

```
Next_Career 2/
├── CLAUDE.md                          ← このファイル（ワークフロー定義）
├── 応募者情報/
│   ├── 履歴書_<応募者名>.pdf
│   ├── 職務経歴書_<応募者名>_<応募先名>.pdf
│   └── その他資料（資格証明書、ポートフォリオ等）
│
└── 応募対象会社/
    └── <会社名>/
        ├── 募集情報/
        │   ├── 募集要項_<会社名>.pdf
        │   └── 求人票・会社資料
        │
        ├── 調査結果/
        │   ├── 01_組織・業界・職種調査.md
        │   ├── 02_選考傾向・面接頻出質問.md
        │   └── 03_面接官プロファイル.md
        │
        └── 面接対策/
            ├── 01_面接/（1回勝負の場合）
            │   ├── 01_想定問答集.md           ← 詳細原本
            │   ├── 02_自己PR案.md             ← 詳細原本
            │   ├── 03_逆質問集.md             ← 詳細原本
            │   ├── 04_事前準備チェックリスト.md ← 詳細原本
            │   └── スライド/
            │       ├── 01_想定問答集_slides.md
            │       ├── 01_想定問答集_slides.pdf  ← 当日持参・チートシート
            │       ├── 02_自己PR案_slides.md
            │       ├── 02_自己PR案_slides.pdf    ← 当日持参・チートシート
            │       ├── 03_逆質問集_slides.md
            │       ├── 03_逆質問集_slides.pdf    ← 当日持参・チートシート
            │       ├── 04_事前準備チェックリスト_slides.md
            │       └── 04_事前準備チェックリスト_slides.pdf ← 当日持参・チートシート
            │
            ├── 02_一次面接/（多段階の場合）
            ├── 03_二次面接/
            └── 04_最終面接/
```

---

## 🚀 ワークフロー実行手順

### Step 0｜初期ヒアリング（必須）

新しい応募案件をスタートするとき、ユーザーに以下を必ず確認する:

1. **選考フロー**：面接は何回か？（1回勝負 / 一次＋二次 / 一次＋二次＋最終 など）
2. **面接官情報**：判明しているか？（氏名・役職 or 未判明）
3. **応募者情報の場所**：`応募者情報/` 配下のどのファイルか
4. **応募先情報の場所**：`応募対象会社/<会社名>/募集情報/` 配下のどのファイルか
5. **特別な要望**：出力形式、強調したい点、避けたい話題など

**重要**：選考フローが判明しない場合は、募集要項を読んで推定し、最後にユーザーに確認する。

### Step 1｜応募者・応募先の情報読み込み

- `応募者情報/` 配下の **全PDFを Read** で読み込み、応募者プロファイルを内部サマリ化
  - 氏名、年齢、居住地、職歴（各社の在職期間と役割）、資格、志望動機、強み・弱み
  - **想定リスク質問**：短期離職、ブランク、年齢、職種転換、キャリアの一貫性の疑問点
- `応募対象会社/<会社名>/募集情報/` 配下の **全ファイルを Read** で読み込み、応募先を理解
  - 組織名、所在地、責任者、職種、雇用形態、給与、選考フロー、求める人物像

### Step 2｜組織・業界・職種の徹底調査

WebFetch / WebSearch / Context7 を活用し、以下を調査する:

**調査項目**
1. 組織の理念・ミッション・ビジョン・バリュー
2. 直近プレスリリース・公式HPニュース
3. 組織SNSアカウント（X / Facebook / YouTube / LinkedIn）の直近発信
4. WEBニュース記事・口コミ（OpenWork・転職会議など）
5. 業界動向（競合、市場環境、政策動向）
6. 職種の実態（業務内容、KPI、1日の流れ、求められるスキル）
7. 選考傾向の調査（面接で聞かれる定番質問、通過者体験談、落選パターン）
8. 求める人物像の言語化（募集要項から明示要件＋暗黙要件を抽出）

**成果物**
- `調査結果/01_組織・業界・職種調査.md`
- `調査結果/02_選考傾向・面接頻出質問.md`

### Step 3｜面接官リサーチ

**面接官が判明している場合**
- 氏名・役職を起点に、以下を検索:
  - 経歴・実績・出身地・出身校
  - インタビュー記事・登壇スピーチ・寄稿
  - SNS発信（X / Facebook / YouTube / LinkedIn）
  - 人柄・価値観・関心テーマ・専門領域

**面接官が未判明の場合**
- 責任者（代表、所長、部門長）の公開情報を調査
- 配属部署の一般的な役職像から「想定プロファイル」を構築
- 「刺さるキーワード」「減点される言葉」を抽出

**成果物**
- `調査結果/03_面接官プロファイル.md`

**プライバシー配慮**：公開情報のみ使用。SNSの非公開情報・個人の評判などは収集しない。

### Step 4｜面接対策成果物の生成（面接1回あたり4ファイル）

各面接（フェーズ）ごとに、以下4ファイルを `面接対策/<NN>_<面接名>/` に生成する:

#### ① `01_想定問答集.md`
カテゴリ別に **最低30問以上** の想定問答を収録:

- **カテゴリA：導入・定番質問**（自己紹介、道中の様子、きっかけ）
- **カテゴリB：志望動機**（なぜこの会社／職種／業界か）
- **カテゴリC：職務経歴の掘り下げ**（成功事例、退職理由、ブランク）
- **カテゴリD：業務理解・職種特化質問**
- **カテゴリE：組織適性・価値観**（公務員倫理、社風フィット）
- **カテゴリF：リスク質問**（年齢、短期離職、職種転換、家族理解など）
- **カテゴリG：人物・価値観**（強み弱み、10年後、休日の過ごし方）
- **カテゴリH：締め**（逆質問、入職日、健康状態）

**回答形式**
- STAR法 / PREP法で構造化
- 実際に話せる長さ（30-90秒）の口語
- 応募者固有の職歴・エピソードを必ず織り込む
- リスク質問には「隠さず、前向きに納得させる」回答を用意

#### ② `02_自己PR案.md`
- **60秒版（約350字）**：簡潔に聞かれたとき
- **90秒版（約500字、推奨デフォルト）**：正面から聞かれたとき
- **3分版（約900字）**：詳しく聞かれたとき

**共通の設計ポイント**
- 軸になる強み1フレーズを最初と最後に配置
- 応募者の職歴3つ（または資格）を柱にする
- 求人要件との一致を明示する設計メモを末尾に添える
- NG表現（一生懸命頑張ります／自信があります 等）のリストを添える

#### ③ `03_逆質問集.md`
- **カテゴリ別に10問以上**:
  - 業務理解を深める質問
  - 貢献意欲・熱意を示す質問
  - 組織理解を示す質問
  - 長期貢献の意志を示す質問
- 各質問に **狙い（なぜこれを聞くか）** を添える
- **NG逆質問**（待遇だけ、調べれば分かること、批判的、特にありません 等）のリストを必ず含める
- 当日の使い分け戦略（時間別、面接官タイプ別）を添える

#### ④ `04_事前準備チェックリスト.md`
- **面接3日前まで**：書類・知識・服装・メンタル準備
- **面接前日**：最終確認、持ち物パッキング、心の準備
- **面接当日・朝**：身だしなみ、移動、到着
- **面接当日・入室〜退室**：挨拶・マナー・面接中の注意点・逆質問タイミング
- **面接後**：記録、振り返り、お礼メールの可否
- **合否連絡期間**：待機中の心構え、内定時／不採用時の対応
- **緊急時対応**：遅刻、体調不良、書類忘れ

### Step 5｜スライドPDF生成（面接1回あたり4 PDF）

Step 4 の各 `.md` を元に、`スライド/` ディレクトリへ **Marp形式スライド＋PDF** を生成する。これが**当日持参するチートシートの最終形**。別途チートシートMDは作成しない。

#### Marpスライドの設計指針

**基本原則**
- **内容は要約しない**：詳細原本（Step 4）の内容をそのままスライドに展開する
- **ページ数は元の約半分を目標**：レイアウト工夫のみでコンパクト化。削減は禁止
- **16:9キャンバス（1280×720px）**を前提に、フォント・余白を最適化する

**コンパクト化の技法**（実証済み。必ず適用する）

| 技法 | 効果 | 実装方法 |
|---|---|---|
| カテゴリ区切りスライドを廃止 | 8〜10枚削減 | 各Q&Aの先頭にカテゴリバッジ（`<span>`）を埋め込む |
| Q&Aを2問1スライドにペアリング | 多数削減 | `<div class="sep"></div>` で区切る（`---` は使わない） |
| 短い項目は3問1スライドにまとめる | さらに削減 | `### Q番号.` (h3) でサブ見出し化 |
| 参照スライドを2列グリッドにまとめる | 2〜4枚削減 | `<div class="two-col">` + CSS Grid |
| 末尾のクロージングスライドを廃止 | 1枚削減 | — |

> **ペアリングの判断基準**：回答本文が4行以下 → 2問ペア可。5行以上 → 単独スライド。

**必須CSSクラス（全4ファイル共通 `style:` ブロックに定義）**

```css
/* 区切り線（新スライドを作らずに2問を視覚分離する） */
.sep { border-top: 2px dashed #93c5fd; margin: 10px 0; }

/* 2列グリッド（参照スライド・対比スライド用） */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }

/* コンパクト余白 */
section { padding: 32px 46px; font-size: 16px; }
blockquote { font-size: 14.5px; }
.tip { font-size: 12px; }
```

**統一デザイン**（全4ファイル共通）
- テーマ：ネイビー×ブルーのグラデーション（#0b1e4d → #3b82f6）
- フォント：`Hiragino Kaku Gothic ProN`, `Yu Gothic`, `Meiryo`
- タイトルスライド：グラデーション背景（カテゴリ仕切りスライドは廃止）
- 💡 ヒントボックス：アンバー（#fef3c7）
- 🚫 NGボックス：レッド（#fef2f2）
- ✅ チェックボックス：グリーン（#ecfdf5）
- ヘッダー：ファイル名 ｜ 応募先名 面接対策
- フッター：応募者名 ｜ 面接日 ｜ 職種名

**ページ数の目安（参考）**

| ファイル | 内容量 | 目標ページ数 |
|---|---|---|
| 01_想定問答集 | 30〜40問 | 25〜35ページ |
| 02_自己PR案 | 3パターン＋付録 | 15〜20ページ |
| 03_逆質問集 | 10〜15問＋付録 | 18〜22ページ |
| 04_事前準備チェックリスト | 時系列7フェーズ | 18〜25ページ |

#### 生成ファイル

```
スライド/
├── 01_想定問答集_slides.md
├── 01_想定問答集_slides.pdf    ← チートシート（最終成果物）
├── 02_自己PR案_slides.md
├── 02_自己PR案_slides.pdf      ← チートシート（最終成果物）
├── 03_逆質問集_slides.md
├── 03_逆質問集_slides.pdf      ← チートシート（最終成果物）
├── 04_事前準備チェックリスト_slides.md
└── 04_事前準備チェックリスト_slides.pdf ← チートシート（最終成果物）
```

#### PDF変換コマンド

```bash
SLIDES_DIR="<面接フェーズフォルダのパス>/スライド"

# 4ファイルを順次変換（並列だと npx が競合する場合あり）
npx @marp-team/marp-cli --pdf "${SLIDES_DIR}/01_想定問答集_slides.md" \
  -o "${SLIDES_DIR}/01_想定問答集_slides.pdf"
npx @marp-team/marp-cli --pdf "${SLIDES_DIR}/02_自己PR案_slides.md" \
  -o "${SLIDES_DIR}/02_自己PR案_slides.pdf"
npx @marp-team/marp-cli --pdf "${SLIDES_DIR}/03_逆質問集_slides.md" \
  -o "${SLIDES_DIR}/03_逆質問集_slides.pdf"
npx @marp-team/marp-cli --pdf "${SLIDES_DIR}/04_事前準備チェックリスト_slides.md" \
  -o "${SLIDES_DIR}/04_事前準備チェックリスト_slides.pdf"
```

> 💡 `npx @marp-team/marp-cli` はインストール不要。Node.js が入っていれば即実行可能。

### Step 5-B｜統合チートシートPDF生成（代替オプション）

Marpスライド（Step 5）の代わりに、**A4縦1枚に情報を集約した統合チートシートPDF** を生成する手法。
面接直前に手元で見返す用途に特化しており、4ファイル分割ではなく1ファイルに全情報をまとめる。

#### 使用技術
- **HTML → Puppeteer → PDF**（Marp不使用）
- Chrome: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- 作業ディレクトリ：`/tmp/pdf_gen/`（`npm install puppeteer` を実行して使う）

#### ファイル構成

```
/tmp/pdf_gen/
├── cheatsheet.html   ← デザイン済みHTML
└── generate.js       ← Puppeteer変換スクリプト
```

`generate.js` の基本形：

```js
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    args: ['--no-sandbox']
  });
  const page = await browser.newPage();
  await page.goto('file:///tmp/pdf_gen/cheatsheet.html', { waitUntil: 'networkidle0' });
  await page.pdf({
    path: '出力先フルパス.pdf',
    format: 'A4',
    printBackground: true,
    margin: { top: '0mm', bottom: '0mm', left: '0mm', right: '0mm' }
  });
  await browser.close();
})();
```

#### セクション構成（標準版）

| # | セクション | 色テーマ |
|---|---|---|
| 1 | ヘッダー（会社名・応募者・応募情報＋メタチップ） | 赤系グラデーション |
| 2 | コアフレーズ（左ボーダー強調） | オレンジ |
| 3 | 3本柱（番号付きテーブル） | ブルー |
| 4 | カテゴリ別キーワード速習（▸箇条書き） | グリーン |
| 5 | リスク対応カード5枚（2列グリッド） | レッド |
| 6 | NG表現リスト（NG/OK対比テーブル） | オレンジ |
| 7 | 逆質問ベスト3＋狙い | パープル |
| 8 | Web面接直前チェックリスト（3列） | ティール |
| 9 | フッター格言 | ダークネイビー |

面接概要メール（評価軸・頻出質問・不採用傾向）が手元にある場合は、逆質問・チェックリストを省略し、代わりに以下を追加：
- 評価軸バーグラフ（重要度を色分けで可視化）
- 頻出質問セクション（2列で詳細Q&A）
- 不採用傾向と逆手に取る対策
- 自己PR3パターン（3列グリッド）
- 出力ファイル名：`00_チートシート_1次面接版.pdf`

#### デザインルール
- **フォント**：Hiragino Kaku Gothic ProN / Yu Gothic、本文8〜8.5pt
- **カード構造**：`card-head`（色帯）＋`card-body` の2層
- **グリッド**：`grid-template-columns: 1fr 1fr` 基本、フルワイドは `grid-column: 1/-1`
- **色の役割**：赤＝リスク・重要、青＝情報・柱、緑＝OK・カテゴリ、紫＝PR、オレンジ＝警告・NG

#### コアフレーズの型
```
[応募者の強み①] × [応募者の強み②] → [求人が求める成果] を同時に実現する
```

#### リスク対応カードの型
```
事実を認める → 積極的な意味付け → 今への橋渡し
```

#### 出力先
```
応募対象会社/<会社名>/面接対策/00_チートシート.pdf
応募対象会社/<会社名>/面接対策/00_チートシート_1次面接版.pdf  ← 面接概要メールあり時
```

---

### Step 6｜仕上げレビュー

全成果物が揃ったら、以下を確認:

- [ ] 応募者の職歴・資格・志望動機との整合性
- [ ] 回答例の矛盾・アピール不足・リスク質問の抜け漏れ
- [ ] 組織の理念・面接官の価値観との共鳴ポイントの織り込み
- [ ] 業界・職種固有の観点の反映
- [ ] 「話せる長さ・言い回し」になっているか
- [ ] 求人要件との対応関係が明示されているか
- [ ] **スライドPDF4ファイルがすべて開けること（破損確認）**

---

## 🧭 重要な設計原則

### 1. 応募者固有のリスクを先回り
どの応募者にも必ずあるリスク（年齢、短期離職、ブランク、職種転換、家族理解など）を隠さず、納得感ある説明を用意する。

### 2. 面接官が誰でも止まらない
面接官未判明でも、役職・部署・組織ミッションから想定プロファイルを構築して進める。

### 3. 業界・組織特有の観点を織り込む
民間企業・公務員・医療・NPO など、それぞれに固有の評価軸がある。
汎用テンプレのままでは不十分。**毎回、業界特有の調査観点を追加する**。

例：
- **公務員**：中立公正、個人情報取扱、法令遵守、服務規律
- **医療・介護**：患者安全、チーム医療、専門性の維持
- **スタートアップ**：変化耐性、自走力、ビジョン共感
- **外資系**：英語力、実績の数値化、ロジカル思考
- **老舗大企業**：社風適合、長期貢献意欲、上下関係

### 4. 「話せる長さ」で書く
面接は口頭の場。書面の文章ではなく、30-90秒で口頭で自然に話せる **口語** に整える。

### 5. プライバシー配慮
面接官調査は公開情報（公式HP、プレスリリース、公開SNS、インタビュー記事）に限定。非公開情報の収集はしない。

### 6. 他応募案件で再利用可能に
ディレクトリ構造、成果物テンプレート、調査観点を **汎用化** し、別の応募先でも同じ手順で動かせるようにする。

---

## 👥 専門エージェントチーム（9体制）

`.claude/agents/` に9名の専門エージェントを配置済み。`interview-director` を起動すれば全工程を分担実行する。

| # | エージェント | 担当 | Step | 使用Skill |
|---|---|---|---|---|
| 1 | **interview-director** | 司令塔・ヒアリング・タスク分配・進捗管理 | 0, 1 | `project-flow-ops`, `claude-md-improver` |
| 2 | **company-researcher** | 組織・業界・職種の徹底Web調査 | 2 | `market-research`, `deep-research`, `exa-search`, `documentation-lookup` |
| 3 | **interviewer-profiler** | 面接官プロファイル（判明/想定） | 3 | `deep-research`, `exa-search`, `market-research` |
| 4 | **qa-architect** | 想定問答集（カテゴリA〜H、30問以上） | 4 ① | `article-writing`, `content-engine`, `brand-voice` |
| 5 | **self-pr-writer** | 自己PR案（60/90秒/3分） | 4 ② | `article-writing`, `brand-voice` |
| 6 | **counter-questioner** | 逆質問集（10問以上＋NG＋戦略） | 4 ③ | `article-writing`, `content-engine` |
| 7 | **prep-coach** | 事前準備チェックリスト（時系列7フェーズ） | 4 ④ | `article-writing`, `content-engine` |
| 8 | **slide-designer** | コンパクトMarpスライド＋PDF | 5 | `frontend-slides`, `frontend-design`, `design-system`, `pptx` |
| 9 | **quality-reviewer** | 独立品質レビュー（6観点） | 6 | `verification-loop`, `eval-harness` |

### 並列実行フロー

```
interview-director（Step 0/1）
  ↓
company-researcher ＋ interviewer-profiler （Step 2+3 並列）
  ↓
qa-architect ＋ self-pr-writer ＋ counter-questioner ＋ prep-coach （Step 4 並列）
  ↓
slide-designer（Step 5）
  ↓
quality-reviewer（Step 6）
  ↓
interview-director（最終報告）
```

### 起動方法

```
@interview-director を起動して、新しい面接対策をチームで進めて
```

---

## 🛠 使用ツール（推奨）

| 用途 | ツール |
|---|---|
| PDF/ファイル読み込み | Read |
| Web調査（公式HP、ニュース、インタビュー） | WebFetch |
| Web検索（面接官・選考傾向・口コミ） | WebSearch |
| ライブラリ/制度ドキュメント | Context7（mcp__plugin_ecc_context7__query-docs） |
| SNSリサーチ | WebFetch + WebSearch |
| 成果物出力 | Write |
| PDF変換（Marp → PDF） | Bash（`npx @marp-team/marp-cli --pdf`） |
| ユーザーへの追加ヒアリング | AskUserQuestion |

---

## ✅ 成果物の品質チェックリスト（End-to-End）

全応募案件で共通の最終検証:

**調査フェーズ（Step 2〜3）**
1. [ ] 調査結果3ファイルがすべて生成されている
2. [ ] 業界・組織固有の選考観点が反映されている
3. [ ] 面接官プロファイル（または想定プロファイル）が生成されている

**面接対策原本（Step 4）**
4. [ ] 面接対策4 MD ファイルが面接回数分だけ生成されている
5. [ ] 想定問答集に以下が含まれている:
   - 定番質問 15問以上
   - 職種特化質問 10問以上
   - 組織特化質問 5問以上
   - リスク対策Q&A（応募者固有のリスクすべて）
6. [ ] 自己PR案が60秒／90秒／3分の3パターン揃っている
7. [ ] 逆質問集が10問以上、NG逆質問の注意書きあり
8. [ ] 応募者の固有の職歴・資格が回答例に具体的に反映されている
9. [ ] 面接官プロファイルの価値観を反映した質問・回答例が含まれている
10. [ ] 事前準備チェックリストが時系列で網羅されている

**スライドPDF（Step 5）**
11. [ ] `スライド/` に `_slides.md` が4ファイル生成されている
12. [ ] `スライド/` に `_slides.pdf` が4ファイル生成されている
13. [ ] 各PDFが正常に開けること（破損・文字化け確認）
14. [ ] **別途チートシートMDは作成しない**（PDFがチートシートの最終形）
15. [ ] ページ数が目安範囲内（01:25〜35 / 02:15〜20 / 03:18〜22 / 04:18〜25）
16. [ ] カテゴリ区切りスライド・クロージングスライドが廃止されている（ページ数節約）
17. [ ] 短いQ&Aは2〜3問ペアリング済み、`.sep` 区切り線が機能している

---

## 📝 新規応募案件を始めるときのプロンプト例

```
新しい応募案件の面接対策をお願いします。

【応募者】
応募者情報/ 配下のPDFを読んでください。

【応募先】
応募対象会社/<会社名>/募集情報/ 配下のPDFを読んでください。

【選考フロー】
面接1回 / 一次＋最終 / その他（詳細記載）

【面接官】
判明している → 氏名・役職を記載
未判明 → 「未判明」と記載

【特別な要望】
（あれば）

CLAUDE.md のワークフローに従って、以下をすべて生成してください：
- 調査結果3ファイル（01_組織・業界・職種調査 / 02_選考傾向 / 03_面接官プロファイル）
- 面接対策4ファイル（01_想定問答集 / 02_自己PR案 / 03_逆質問集 / 04_事前準備チェックリスト）
- スライドMD 4ファイル ＋ スライドPDF 4ファイル（スライド/ ディレクトリ）
```

---

## 🔄 完了した応募案件一覧（実績）

| 応募先 | 応募者 | 面接日 | 選考フロー | 状態 |
|---|---|---|---|---|
| 東京労働局 飯田橋公共職業安定所（就職支援コーディネーター） | 渡邉 珠美 | 2026/4/27 | 面接1回 | ✅ 準備完了 |

---

## 📚 参考：過去案件から学んだこと

### ハローワーク（公的機関）面接の特殊性
- 「なぜ民間でなく公的機関か」を最も厳しく問われる
- 国家公務員法第38条の欠格事由認識は必須
- 中立公正・個人情報取扱の理解が評価軸の中核
- 数値目標への前向きさ＋「公共のための数値」というスタンス
- お礼メールは送らない方が賢明（公平性の観点）

### 54歳以上の面接対策
- 年齢を「武器化」（落ち着き、人生経験、多様な接遇経験）
- 短期離職には「各社で学んだこと」を整理
- ブランク期間は「前向きに何をしていたか」を具体化
- 体力・適応力への懸念には「実績＋謙虚さ」で回答

### 医療・福祉分野への応募
- 介護有効求人倍率、2026年度の国家プロジェクトを把握
- 業界固有の制度理解（介護保険、処遇改善加算、訪問看護）
- 「利用者の生き方に寄り添う」「人の命と生活を支える」キーワード

### Marpスライドのコンパクト化（実証済み技法）
- **`<div class="sep"></div>`** — `---` や `<hr>` は新スライドを作る。ペアQ&A内の区切りはこのdivで。
- **カテゴリ仕切りスライドは廃止** — Q&A先頭の小バッジで代替。8〜10枚削減できる。
- **CSS Grid 2列** — 対比・参照系スライド（5原則vs磁力ワード、時間別vs状況別など）は `display: grid; grid-template-columns: 1fr 1fr` で1枚に収める。
- **h3（`###`）でサブ見出し化** — 1スライド内に複数Q&Aを入れるとき、h1（`#`）ではなくh3を使う。h1はMarpのスライドタイトルとして大きすぎる。
- **フォント16px・余白32px** — デフォルト（22px・70px相当）から削減してもA4印刷・モニター閲覧では十分読める。
- **実績ページ数**（01_想定問答集57→29 / 02_自己PR案34→17 / 03_逆質問集44→20 / 04_事前準備50→21）

---

## 🚀 Webアプリ開発チーム（10体制）

このプロジェクトには、**面接対策チーム**（9体）とは別に、
**転職支援Webアプリ（Naitei.ai 等）の開発専用チーム** が `.claude/agents/webapp-*.md` に整備されています。

### チーム構成

| # | エージェント | 担当Step | 主要スキル |
|---|---|---|---|
| 1 | **webapp-director** | Step 0〜6 統括 | `team-builder`, `agentic-engineering`, `autonomous-agent-harness`, `council`, `blueprint` |
| 2 | **webapp-product-planner** | Step 1 PRD | `prp-prd`, `product-lens`, `product-capability`, `market-research` |
| 3 | **webapp-system-architect** | Step 1 システム設計 | `hexagonal-architecture`, `api-design`, `architecture-decision-records`, `nextjs-turbopack`, `security-review` |
| 4 | **webapp-ui-ux-designer** | Step 1 UI設計 | `frontend-design`, `design-system`, `frontend-patterns`, `liquid-glass-design` |
| 5 | **webapp-ai-engineer** | Step 1 AI連携 | `claude-api`, `prompt-optimizer`, `cost-aware-llm-pipeline`, `iterative-retrieval` |
| 6 | **webapp-frontend-dev** | Step 3 フロント実装 | `nextjs-turbopack`, `frontend-patterns`, `bun-runtime`, `coding-standards` |
| 7 | **webapp-backend-dev** | Step 3 バック実装 | `backend-patterns`, `api-design`, `coding-standards`, `git-workflow` |
| 8 | **webapp-tdd-engineer** | Step 3〜4 テスト | `tdd-workflow`, `e2e-testing`, `ai-regression-testing` |
| 9 | **webapp-devops** | Step 5 デプロイ | `deployment-patterns`, `docker-patterns`, `git-workflow`, `github-ops`, `canary-watch` |
| 10 | **webapp-quality-gate** | Step 2/6 品質ゲート | `security-review`, `santa-method`, `verification-loop`, `code-review`, `click-path-audit` |

### 自律実行フロー

```
Step 0｜要件ヒアリング（webapp-director）
   ↓
Step 1｜設計フェーズ（4体並列）
   ├─ product-planner    → PRD.md
   ├─ system-architect   → system-architecture.md, api-design.md
   ├─ ui-ux-designer     → ui-design.md
   └─ ai-engineer        → ai-integration-design.md
   ↓
Step 2｜設計レビュー（quality-gate）
   ↓ santa-method（独立2回レビュー）で承認
Step 3｜実装フェーズ（3体並列）
   ├─ frontend-dev → コンポーネント・画面
   ├─ backend-dev  → API Routes・AI連携
   └─ tdd-engineer → テスト先行（並走）
   ↓
Step 4｜統合テスト（tdd-engineer + quality-gate）
   ↓
Step 5｜デプロイ（devops）
   ↓
Step 6｜最終承認（quality-gate）
   ↓
ユーザー報告（webapp-director）
```

### 起動方法

```
@webapp-director を起動して、Webアプリの設計→実装→テスト→デプロイまで自律的に進めて。
```

### 出力先（プロジェクト規約）

- **設計書**：`webapp-design/`（PRD, system-architecture, api-design, ui-design, ai-integration-design, design-review）
- **実装**：`webapp/`（Next.jsプロジェクト一式）
- **品質レポート**：`webapp/docs/quality-report.md`
- **デプロイ手順**：`webapp/docs/DEPLOY.md`、`webapp/docs/RUNBOOK.md`

### 共存原則

- **面接対策チーム** と **Webアプリ開発チーム** は別チームとして並列稼働可能
- 両チームを同時起動しないこと（チーム名衝突防止）
- 面接対策の知見（CLAUDE.md上部の「過去案件から学んだこと」）は、
  Webアプリ開発時の **ドメイン知識**として参照される

---

このCLAUDE.mdは、案件が増えるたびに学びを追記し、ワークフローを進化させていく。
