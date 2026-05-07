# CLAUDE.md

このファイルは Claude Code がコードを扱う際の指示を提供します。

---

## 🌐 プロジェクト概要

転職支援Webアプリ「Naitei.ai」の開発プロジェクト。
書類添削（Step 3）と面接対策（Step 4: 想定問答・自己PR・逆質問・チェックリスト）をAIで生成するWebサービス。
- **フロントエンド**: `webapp/`（Next.js 14 App Router + TypeScript）→ Vercel
- **バックエンド**: `main.py`（FastAPI）→ Railway
- **現フェーズ**: UI/UXデザインブラッシュアップ・出力形式改善

| 環境 | URL |
|---|---|
| **本番（フロント）** | https://nextcareer.pro （パスワードゲートあり） |
| **Railway（バック）** | https://naitei-backend-production.up.railway.app |
| Vercel Dashboard | https://vercel.com/dashboard |
| Railway Dashboard | https://railway.app |

> **パスワードゲート**: `webapp/middleware.ts` が全リクエストをチェック。未認証時は `/gate` へリダイレクト。Cookie `naitei_auth` で7日間認証を維持。パスワードは Vercel 環境変数 `BASIC_AUTH_PASS`（デフォルト: `1616`）。

---

## ⚙️ よく使うコマンド

```bash
# フロントエンド（cd webapp から実行）
npm run dev          # 開発サーバー（localhost:3000）
npm run build        # 本番ビルド
npm run test         # ユニットテスト（Vitest）
npm run test:watch   # watchモード（開発中推奨）
npm run test:e2e     # E2Eテスト（Playwright）
npm run lint         # ESLint

# バックエンド
uvicorn main:app --reload            # 開発サーバー（localhost:8000）
pytest test_main.py -v               # 全テスト
pytest test_main.py::test_名前 -v   # 単一テスト
```

---

## 📐 コーディング規約

### TypeScript / React
- **型定義**: `types/` に集約（`applicant.ts` / `api.ts` / `ai.ts`）、`any` 使用禁止
- **import パス**: `@/types`, `@/lib`, `@/components` 推奨（相対パス避ける）
- **状態管理**: サーバー状態→TanStack Query / クライアント状態→Zustand / フォーム→React Hook Form
- **コンポーネント**: 機能単位ディレクトリ構成、200-400行以下
- **ストリーミング**: Vercel AI SDK `streamText()` + `toDataStreamResponse()`

### テスト（80%+ 必須）
- **単体テスト**: `components/__tests__/` または `src/lib/__tests__/`
- **E2E**: `e2e/golden-path.spec.ts`（Playwright）
- RED → GREEN → REFACTOR の順序を守る

---

## 🎨 UIデザイン方針（現フェーズ優先）

> 詳細ルール → `.claude/rules/project/ui-design.md` 参照

- **UIライブラリ**: shadcn/ui + Tailwind CSS v3
- **デザイントークン**: `app/globals.css` の OKLCH カラー変数優先（ハードコード禁止）
- **アイコン**: Lucide React 統一 / **アンチパターン**: テンプレートそのまま使用禁止

---

## 🚀 デプロイ前チェックリスト（Webアプリ専用）

- [ ] `npm run build` 成功（本番ビルド検証）
- [ ] `npm run test` テストカバレッジ 80%+
- [ ] `npm run lint` ESLintエラーなし
- [ ] 環境変数が `.env.example` に記載済み
- [ ] GitHub Actions CI 全ステージ通過
- [ ] Vercel Preview URL 確認済み

**CI/CD**: `.github/workflows/ci.yml`（unit-test → e2e-test → deploy の順）
**注意**: 各 Job の `working-directory` は明示しない（リポジトリルートを使用）

---

## 📚 プロジェクトドキュメント

| ドキュメント | パス | 内容 |
|---|---|---|
| システム仕様書 | `docs/SPECIFICATION.md` | API・型・コンポーネント・セキュリティの全詳細 |
| アーキテクチャ図 | `docs/architecture.md` | 非エンジニア向け構成図・データフロー（Mermaid） |
| 引き継ぎ要約 | `docs/handoff-summary.md` | フェーズ移行時の着手ポイント・課題一覧 |
| UIデザインルール | `.claude/rules/project/ui-design.md` | shadcn/ui・OKLCH・モーション詳細ルール |

> **面接対策ワークフロー** → `~/Desktop/Interview_Workflow/` で別途 Claude Code を起動
