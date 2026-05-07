# 新フェーズ引き継ぎ要約

フェーズ移行時（またはセッション開始時）に新しいエージェント・担当者が最短でコンテキストを把握するためのサマリー。

**現フェーズ**: UIデザインブラッシュアップ ＋ 出力形式・添削ロジック改善

---

## 1. プロジェクト全体像

詳細なシステム仕様は以下の2ドキュメントを参照：

| ドキュメント | 用途 |
|---|---|
| [`docs/SPECIFICATION.md`](SPECIFICATION.md) | 技術仕様（API・型・コンポーネント・セキュリティ全詳細、928行） |
| [`docs/architecture.md`](architecture.md) | アーキテクチャ図（非エンジニア向け構成図・データフロー、383行） |

### 一言まとめ
- **フロントエンド** (`webapp/`): Next.js 14 App Router → Vercel (`https://nextcareer.pro`)
- **バックエンド** (`main.py`): FastAPI (Python) → Railway
- **AI**: Claude (haiku-4-5) → OpenAI (gpt-4o) → Gemini (gemini-2.5-flash) のカスケード
- **状態管理**: DB なし。`sessionStorage` のみ（`naitei_company` / `naitei_applicant`）
- **通信**: SSE ストリーミング（リアルタイム表示）
- **認証**: Cookie ベースのパスワードゲート（`/gate` ページ、`naitei_auth` Cookie、7日間有効）

---

## 2. 添削ロジックの主要ファイル

### バックエンド

| ファイル | 役割 |
|---|---|
| `main.py` (L1-1227) | 全バックエンド処理。AI連携・プロンプト・PDF生成すべてここに集約 |
| `main.py` → `POST /api/review` | 書類添削エンドポイント。`sse_stream()` 関数でSSE配信 |
| `main.py` → `_markdown_to_pdf_bytes()` | PDF生成。ReportLab + 日本語フォント（HeiseiKakuGo-W5 → NotoSansJP） |

### フロントエンド（添削ロジック周辺）

| ファイル | 役割 |
|---|---|
| `webapp/app/step3/page.tsx` | 書類添削画面。SSEストリーミング受信・タブ表示・PDF DL |
| `webapp/app/api/review/route.ts` | Next.js APIプロキシ。`proxySSE()` でRailwayからの SSE をそのまま中継 |
| `webapp/lib/api-client.ts` | SSE クライアント。`sseStream()` 関数が `event: content/done/error` をパース |
| `webapp/lib/backend.ts` | バックエンドURL解決 + `proxySSE()` + `SSE_HEADERS` |

### API リクエスト/レスポンス型

| ファイル | 内容 |
|---|---|
| `webapp/types/api.ts` | `ReviewRequest`, `ReviewResponse`, `ReviewedDocument`, `ReviewComment` |
| `webapp/types/applicant.ts` | `ApplicantProfile`, `CompanyInfo`, `CareerItem` |

---

## 3. 出力形式改善で解決すべき課題

優先度順：

### 🔴 高優先度

| 課題 | 現状 | 改善方針 |
|---|---|---|
| **Markdownレンダリング** | SSEで流れてくるMarkdownがプレーンテキスト表示 | `react-markdown` 導入 or 手動パース |
| **PDF品質** | ReportLabの日本語レイアウトが崩れることがある | フォント設定の見直し、段落幅の調整 |
| **ストリーミング完了検知** | `event: done` 受信後の UI 状態更新が遅延する場合がある | `useEffect` の cleanup 関数を見直し |

### 🟡 中優先度

| 課題 | 現状 | 改善方針 |
|---|---|---|
| **添削前後の差分表示** | 現在は2タブ（元原稿/添削後）のみ | diff ライブラリ（`diff`パッケージ等）でハイライト表示 |
| **エラー時のリトライ** | SSEエラー時に再試行UIがない | `AbortController` + 再試行ボタン |
| **進捗メッセージの改善** | 固定メッセージ | ストリーミング進捗に応じた動的メッセージ |

---

## 4. UIデザインブラッシュアップの着手ポイント

詳細ルールは [`.claude/rules/project/ui-design.md`](../.claude/rules/project/ui-design.md) 参照。

### 優先着手ページ

| ページ | ファイル | 改善ポイント |
|---|---|---|
| **Step 3（書類添削）** | `webapp/app/step3/page.tsx` | タブのデザイン、ストリーミング中アニメーション、PDF DLボタン |
| **Step 4（面接対策）** | `webapp/app/step4/page.tsx` | 4パネルのレイアウト、カード階層、検索UI |
| **ランディング** | `webapp/app/page.tsx` | ヒーロー訴求力、FAQ デザイン |

### デザイントークン確認

```bash
# 現在のカラートークン一覧を確認
grep -n 'color-primary\|color-secondary\|color-accent' webapp/app/globals.css
```

### shadcn/ui コンポーネント追加手順

```bash
cd webapp
npx shadcn@latest add <component-name>
# 追加後、globals.css のトークンに合わせてスタイル上書き
```

---

## 5. 開発環境の起動

```bash
# フロントエンド（localhost:3000）
cd webapp && npm run dev

# バックエンド（localhost:8000）
uvicorn main:app --reload

# テスト
cd webapp && npm run test:watch   # ユニット（watchモード）
cd webapp && npm run test:e2e     # E2E（Playwright）
```

---

## 6. 環境変数チェック

```bash
# フロントエンド
cat webapp/.env.local   # BACKEND_URL が設定されているか確認

# バックエンド
echo $ANTHROPIC_API_KEY   # Claude API キー
echo $OPENAI_API_KEY      # OpenAI API キー
```
