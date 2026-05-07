---
paths:
  - "応募対象会社/**"
  - "応募者情報/**"
---
# 面接対策ワークフロー（詳細リファレンス）

> CLAUDE.md のインデックスから参照される詳細仕様。

## Step 0｜初期ヒアリング（必須）

新しい応募案件開始時に確認:
1. **選考フロー**: 面接は何回か（1回 / 一次＋二次 / 一次＋二次＋最終）
2. **面接官情報**: 判明しているか（氏名・役職 or 未判明）
3. **応募者情報の場所**: `応募者情報/` 配下のファイル
4. **応募先情報の場所**: `応募対象会社/<会社名>/募集情報/` のファイル
5. **特別な要望**: 出力形式・強調点・避ける話題

## Step 1｜情報読み込み

- `応募者情報/` 全PDF → 氏名・職歴・資格・強み弱み・想定リスク質問を内部サマリ化
- `応募対象会社/<会社名>/募集情報/` 全ファイル → 組織・職種・雇用形態・求める人物像を理解

## Step 2｜組織・業界・職種調査

WebFetch/WebSearch/Context7 で調査 → `調査結果/01_組織・業界・職種調査.md`, `02_選考傾向・面接頻出質問.md` を生成:
1. 組織の理念・MVV・直近プレスリリース
2. SNS発信（X/Facebook/YouTube/LinkedIn）
3. 口コミ（OpenWork・転職会議）
4. 業界動向・競合・政策動向
5. 職種実態（KPI、1日の流れ、スキル）
6. 選考傾向（通過者体験談・落選パターン）

## Step 3｜面接官リサーチ → `調査結果/03_面接官プロファイル.md`

**判明時**: 経歴・インタビュー記事・SNS発信（公開情報のみ）
**未判明時**: 役職・部署・組織ミッションから想定プロファイル構築

## Step 4｜面接対策4ファイル生成（各面接フェーズごと）

`面接対策/<NN>_<面接名>/` に生成:

| ファイル | 内容 |
|---|---|
| `01_想定問答集.md` | カテゴリA〜H、最低30問。STAR/PREP法、30-90秒口語、リスクQ&A含む |
| `02_自己PR案.md` | 60秒/90秒/3分 の3パターン。強み1フレーズを冒頭と末尾に配置 |
| `03_逆質問集.md` | 10問以上 + NG逆質問リスト + 時間別・面接官タイプ別戦略 |
| `04_事前準備チェックリスト.md` | 3日前→前日→当日朝→入室〜退室→面接後→合否待機の時系列 |

### 想定問答カテゴリ
A: 導入・定番 / B: 志望動機 / C: 職務経歴掘り下げ / D: 業務理解・職種特化 / E: 組織適性・価値観 / F: リスク質問 / G: 人物・価値観 / H: 締め

## Step 5｜Marpスライド＋PDF生成

`スライド/` に `_slides.md` + `_slides.pdf` を4ファイル生成（チートシート最終形）。

チートシートMDも並行して `チートシート/` に4ファイル生成（スライドの元原稿として使う）。

> ⚡ **必須**: 新しいスライドファイルを作成するときは、まず
> `.claude/templates/marp-slides-template.md` を Read して、
> frontmatter（`---` 〜 `---`）のCSSブロックをそのままコピーすること。
> ルールに書いたCSSは参照用。実際の転写はテンプレートファイルから行う。

### Marpデザイン仕様（全4ファイル共通）★2026-05確定版★

**基本設定（frontmatter）**
```yaml
---
marp: true
theme: default
paginate: true
size: 16:9
backgroundColor: '#ffffff'
color: '#1f2937'
header: '<タイトル> ｜ <会社名> 面接対策'
footer: '<応募者氏名> ｜ <面接日> ｜ <職種名>'
style: |
  ...（下記CSS）
---
```

**ベースCSS（全ファイル共通・style:ブロックに貼る）**
```css
section {
  font-family: 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', sans-serif;
  padding: 32px 46px; font-size: 16px; line-height: 1.5;
}
/* ===== 特殊スライドクラス ===== */
section.title {
  background: linear-gradient(135deg, #0b1e4d 0%, #1e40af 60%, #3b82f6 100%);
  color: #ffffff; display: flex; flex-direction: column;
  justify-content: center; align-items: center; text-align: center;
}
section.title h1 { font-size: 54px; color: #ffffff; border: none; margin-bottom: 16px; }
section.title h2 { font-size: 24px; color: #bfdbfe; font-weight: normal; border: none; }
section.title p  { font-size: 20px; color: #dbeafe; margin-top: 20px; }
section.core {
  background: #0b1e4d; color: #ffffff;
  display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;
}
section.core h1 { color: #fef3c7; border: none; font-size: 30px; }
section.core .bigbox {
  background: #1e3a8a; border: 3px solid #fbbf24; border-radius: 18px;
  padding: 36px 52px; margin-top: 24px; font-size: 34px; font-weight: bold;
  color: #fef3c7; max-width: 1000px; line-height: 1.4;
}
section.hero {
  background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
  color: #ffffff; display: flex; flex-direction: column; justify-content: center;
}
section.hero h1 { color: #fef3c7; border: none; font-size: 28px; }
section.hero h2 { color: #bfdbfe; font-size: 20px; border: none;
  border-left: 4px solid #fbbf24; padding-left: 12px; margin-top: 12px; }
section.hero blockquote { background: rgba(255,255,255,0.1); border-left: 4px solid #fbbf24; color: #f1f5f9; }
section.mantra {
  background: #0b1e4d; color: #ffffff;
  display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;
}
section.mantra h1 { color: #fef3c7; border: none; font-size: 26px; }
section.mantra .mantra-box {
  background: #1e3a8a; border: 2px solid #fbbf24; border-radius: 14px;
  padding: 28px 40px; margin-top: 20px; font-size: 18px;
  color: #f1f5f9; line-height: 2.2; text-align: left; max-width: 900px;
}
/* ===== 本文スタイル ===== */
h1 { color: #0b1e4d; border-bottom: 3px solid #3b82f6; padding-bottom: 6px;
  font-size: 22px; margin-bottom: 10px; margin-top: 0; }
h2 { color: #1e40af; font-size: 18px; border-left: 5px solid #3b82f6;
  padding-left: 12px; margin-top: 12px; margin-bottom: 4px; }
h3 { color: #1e3a8a; font-size: 15px; margin-top: 10px; margin-bottom: 3px; }
strong { color: #b91c1c; font-weight: 700; }
blockquote {
  border-left: 5px solid #3b82f6; background: #eff6ff;
  padding: 10px 16px; margin: 8px 0; border-radius: 0 8px 8px 0;
  font-size: 15px; line-height: 1.65; color: #1f2937;
}
table { border-collapse: collapse; margin: 8px 0; width: 100%; font-size: 14px; }
th { background: #1e40af; color: #ffffff; padding: 7px 10px;
  border: 1px solid #1e3a8a; text-align: center; }
td { padding: 7px 10px; border: 1px solid #cbd5e1; background: #ffffff; }
tr:nth-child(even) td { background: #f1f5f9; }
/* ===== ユーティリティクラス ===== */
.tip    { background: #fef3c7; border-left: 5px solid #f59e0b; padding: 7px 14px;
  margin: 8px 0; border-radius: 0 8px 8px 0; font-size: 13px; color: #7c2d12; }
.recommend { background: #ecfdf5; border: 2px solid #10b981; padding: 10px 18px;
  margin: 8px 0; border-radius: 10px; font-size: 14px; }
.ng     { background: #fef2f2; border-left: 5px solid #dc2626; padding: 10px 16px;
  margin: 8px 0; border-radius: 0 8px 8px 0; color: #7f1d1d; font-size: 14px; }
.ok     { background: #ecfdf5; border-left: 5px solid #10b981; padding: 7px 14px;
  margin: 8px 0; border-radius: 0 8px 8px 0; font-size: 13px; color: #065f46; }
.magnet { background: #fffbeb; border: 3px dashed #f59e0b; padding: 18px 24px;
  margin: 12px 0; border-radius: 12px; font-size: 18px; color: #78350f; line-height: 2; }
.q-card { background: #f8faff; border: 1px solid #bfdbfe; border-radius: 10px;
  padding: 12px 18px; margin: 8px 0; font-size: 14px; }
.q-card h3 { color: #1e40af; margin-top: 0; }
.flow   { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px;
  padding: 12px 20px; margin: 8px 0; font-size: 14px; line-height: 1.9; }
.sep    { border: none; border-top: 2px dashed #93c5fd; margin: 10px 0; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
ul, ol  { font-size: 15px; line-height: 1.7; margin: 4px 0; }
li      { margin-bottom: 3px; }
header  { color: #64748b; font-size: 13px; }
footer  { color: #64748b; font-size: 12px; }
```

**スライドクラスの使い分け**

| クラス | 用途 | 背景 |
|---|---|---|
| `<!-- _class: title -->` | 表紙スライド | ネイビー→ブルー グラデーション |
| `<!-- _class: core -->` | コアフレーズ強調（自己PR用）| ダークネイビー + 金枠bigbox |
| `<!-- _class: hero -->` | 重要情報ハイライト（会場情報等）| ネイビーグラデーション |
| `<!-- _class: mantra -->` | 面接直前の呪文（チェックリスト末尾）| ダークネイビー + 金枠mantra-box |
| （クラスなし） | 通常スライド | 白背景 |

**コンパクト化ルール（必須適用）**
- カテゴリ区切りスライド廃止 → Q&A冒頭のバッジ/h2で代替（8〜10枚削減）
- 4行以下の回答は2問1スライドにペアリング（`<div class="sep">` で区切る）
- 末尾の締めスライドは廃止（mantra以外）

**目標ページ数**: 01:25-35 / 02:14-18 / 03:14-18 / 04:16-22

### 各ファイルの構成テンプレート

**01_想定問答集_slides.md**
1. title スライド（表紙）
2. 5原則 & 磁力キーワード
3. Q早見表（カテゴリ × 推奨度）× 2〜3枚
4. Q&A スライド群（2問ペア or 1問ソロ）
5. リスク早見表 + カバレッジチェック表

**02_自己PR案_slides.md**
1. title スライド
2. core スライド（コアフレーズ bigbox）
3. 3バージョン使い分け表
4. 60秒版 本文 + ポイント
5. 90秒版 本文①② + 本文③＋ポイント
6. 3分版 導入＋①前半 / ①エピソード＋②CC / ③接遇＋締め
7. 求人要件対応表
8. 音読練習ポイント
9. NG表現リスト
10. 当日フローチャート
11. 磁力ワード（magnet クラス）

**03_逆質問集_slides.md**
1. title スライド
2. hero スライド（鉄板セット＋絶対NG）
3. 基本方針表
4. 10問一覧表
5. 業務理解質問群（q-card）× 2〜3枚
6. 貢献意欲・組織理解・締め質問群 × 2〜3枚
7. NG逆質問リスト
8. 時間別使い分け戦略（フロー＋シチュエーション表）
9. 話し方テンプレート
10. 面接官タイプ別反応予測 + 差がつくパターン
11. 最終確認リスト

**04_事前準備チェックリスト_slides.md**
1. title スライド
2. hero スライド（面接基本情報・アクセス表）
3. タイムライン早見表
4. 3日前：書類・知識（two-col）
5. 3日前：服装・健康
6. 前日：経路・パッキング（two-col）
7. 当日朝
8. 入室の流れ（flow クラス）
9. 着席後の姿勢・話し方（two-col）+ NG
10. 面接中の応急対応 + 逆質問タイミングフロー
11. 退室の流れ（flow クラス）
12. 面接後・合否連絡（two-col）
13. 緊急時対応
14. 前日夜最終チェック + 第一印象
15. mantra スライド（面接直前の心の呪文）

**PDF変換（`marp` コマンドを使う）**
```bash
SLIDES_DIR="<フェーズフォルダ>/スライド"
marp --pdf "${SLIDES_DIR}/01_想定問答集_slides.md" -o "${SLIDES_DIR}/01_想定問答集_slides.pdf"
marp --pdf "${SLIDES_DIR}/02_自己PR案_slides.md" -o "${SLIDES_DIR}/02_自己PR案_slides.pdf"
marp --pdf "${SLIDES_DIR}/03_逆質問集_slides.md" -o "${SLIDES_DIR}/03_逆質問集_slides.pdf"
marp --pdf "${SLIDES_DIR}/04_事前準備チェックリスト_slides.md" -o "${SLIDES_DIR}/04_事前準備チェックリスト_slides.pdf"
```

> ⚠️ `npx @marp-team/marp-cli` は動作しない。`marp`（Homebrew, `/opt/homebrew/bin/marp`）を使う。
> 並列実行可：各コマンドの末尾に `&` を付けて `wait` で待機するとまとめて速い。

## Step 5-A｜チートシートMD生成（スライドの元原稿）

`チートシート/` に `_チートシート.md` を4ファイル生成。スライドの作成前にまずこちらを作ると内容が整理しやすい。

| ファイル | 内容 |
|---|---|
| `01_想定問答集_チートシート.md` | 全Q&Aの口語テキスト、リスク早見表、カバレッジチェック |
| `02_自己PR案_チートシート.md` | 3バージョン本文、求人要件対応表、NG表現、使い分けフロー、磁力ワード |
| `03_逆質問集_チートシート.md` | 10問の本文と狙い、NG逆質問、時間別戦略、話し方テンプレート |
| `04_事前準備チェックリスト_チートシート.md` | タイムライン、全チェック項目、入退室フロー、緊急時対応、心の呪文 |

> チートシートMDはスライドと同等の内容をMarkdown形式で記載する。スライドはチートシートから内容を抜粋してMarp化する。

## Step 6｜仕上げレビュー

- [ ] 応募者固有の職歴・資格・志望動機との整合
- [ ] 回答例の矛盾・アピール不足・リスクQ&A抜け漏れ
- [ ] 面接官価値観との共鳴ポイント織り込み
- [ ] 「話せる長さ」（30-90秒口語）になっているか
- [ ] PDF 4ファイルが正常に開けること

## 専門エージェントチーム（起動方法）

```
@interview-director を起動して、新しい面接対策をチームで進めて
```

並列フロー: `interview-director (Step0/1)` → `company-researcher + interviewer-profiler (並列)` → `qa-architect + self-pr-writer + counter-questioner + prep-coach (並列)` → `slide-designer` → `quality-reviewer`

## 重要な設計原則

1. **応募者固有リスクを先回り** — 年齢・短期離職・ブランク・職種転換を隠さず前向きに対処
2. **面接官未判明でも止まらない** — 役職・ミッションから想定プロファイルを構築
3. **業界固有の観点を必ず追加** — 公務員:中立公正・法令遵守 / 医療:患者安全・チーム医療 / 外資:数値化・ロジカル思考
4. **口語で書く** — 書面の文章ではなく30-90秒で話せる口語に整える
5. **公開情報のみ使用** — 面接官調査は公式HP・プレスリリース・公開SNS限定

## 新規案件開始プロンプト例

```
新しい応募案件の面接対策をお願いします。

【応募者】応募者情報/ 配下のPDFを読んでください。
【応募先】応募対象会社/<会社名>/募集情報/ 配下のPDFを読んでください。
【選考フロー】面接1回 / 一次＋最終 / その他
【面接官】（氏名・役職 or 未判明）
【特別な要望】（あれば）

調査3ファイル＋対策4ファイル＋スライドPDF 4ファイルを生成してください。
```

## 過去案件の学び

**ハローワーク系**: 「なぜ公的機関か」を最も厳しく問われる。国家公務員法第38条認識必須。お礼メール不要。
**54歳以上**: 年齢を「武器化」（落ち着き・人生経験）。短期離職は「各社で学んだこと」で整理。
**Marpコンパクト化実績**: 01: 57→29ページ / 02: 34→16 / 03: 44→16 / 04: 50→16

**ディレクトリ構成（確定）**
```
面接対策/<NN>_<面接名>/
├── 01_想定問答集.md
├── 02_自己PR案.md
├── 03_逆質問集.md
├── 04_事前準備チェックリスト.md
├── チートシート/
│   ├── 01_想定問答集_チートシート.md
│   ├── 02_自己PR案_チートシート.md
│   ├── 03_逆質問集_チートシート.md
│   └── 04_事前準備チェックリスト_チートシート.md
└── スライド/
    ├── 01_想定問答集_slides.md   ← Marp白背景スタイル
    ├── 01_想定問答集_slides.pdf
    ├── 02_自己PR案_slides.md
    ├── 02_自己PR案_slides.pdf
    ├── 03_逆質問集_slides.md
    ├── 03_逆質問集_slides.pdf
    ├── 04_事前準備チェックリスト_slides.md
    └── 04_事前準備チェックリスト_slides.pdf
```
