---
marp: true
theme: default
paginate: true
size: 16:9
backgroundColor: '#ffffff'
color: '#1f2937'
header: '{{SLIDE_TITLE}} ｜ {{COMPANY_NAME}} 面接対策'
footer: '{{APPLICANT_NAME}} ｜ {{INTERVIEW_DATE}} ｜ {{JOB_TITLE}}'
style: |
  section {
    font-family: 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', sans-serif;
    padding: 32px 46px;
    font-size: 16px;
    line-height: 1.5;
  }
  section.title {
    background: linear-gradient(135deg, #0b1e4d 0%, #1e40af 60%, #3b82f6 100%);
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
  }
  section.title h1 { font-size: 54px; color: #ffffff; border: none; margin-bottom: 16px; }
  section.title h2 { font-size: 24px; color: #bfdbfe; font-weight: normal; border: none; }
  section.title p { font-size: 20px; color: #dbeafe; margin-top: 20px; }
  section.core {
    background: #0b1e4d;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
  }
  section.core h1 { color: #fef3c7; border: none; font-size: 30px; }
  section.core .bigbox {
    background: #1e3a8a;
    border: 3px solid #fbbf24;
    border-radius: 18px;
    padding: 36px 52px;
    margin-top: 24px;
    font-size: 34px;
    font-weight: bold;
    color: #fef3c7;
    max-width: 1000px;
    line-height: 1.4;
  }
  section.hero {
    background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.hero h1 { color: #fef3c7; border: none; font-size: 28px; }
  section.hero h2 { color: #bfdbfe; font-size: 20px; border: none; border-left: 4px solid #fbbf24; padding-left: 12px; margin-top: 12px; }
  section.hero blockquote { background: rgba(255,255,255,0.1); border-left: 4px solid #fbbf24; color: #f1f5f9; }
  section.hero table { font-size: 15px; }
  section.hero th { background: rgba(30,58,138,0.8); color: #fef3c7; }
  section.hero td { background: rgba(255,255,255,0.1); color: #f1f5f9; border-color: #3b82f6; }
  section.hero .star-box { background: rgba(251,191,36,0.2); border: 2px solid #fbbf24; border-radius: 10px; padding: 12px 20px; margin: 8px 0; color: #fef3c7; }
  section.mantra {
    background: #0b1e4d;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
  }
  section.mantra h1 { color: #fef3c7; border: none; font-size: 26px; }
  section.mantra .mantra-box {
    background: #1e3a8a;
    border: 2px solid #fbbf24;
    border-radius: 14px;
    padding: 28px 40px;
    margin-top: 20px;
    font-size: 18px;
    color: #f1f5f9;
    line-height: 2.2;
    text-align: left;
    max-width: 900px;
  }
  h1 {
    color: #0b1e4d;
    border-bottom: 3px solid #3b82f6;
    padding-bottom: 6px;
    font-size: 22px;
    margin-bottom: 10px;
    margin-top: 0;
  }
  h2 {
    color: #1e40af;
    font-size: 18px;
    border-left: 5px solid #3b82f6;
    padding-left: 12px;
    margin-top: 12px;
    margin-bottom: 4px;
  }
  h3 { color: #1e3a8a; font-size: 15px; margin-top: 10px; margin-bottom: 3px; }
  strong { color: #b91c1c; font-weight: 700; }
  blockquote {
    border-left: 5px solid #3b82f6;
    background: #eff6ff;
    padding: 10px 16px;
    margin: 8px 0;
    border-radius: 0 8px 8px 0;
    font-size: 15px;
    line-height: 1.65;
    color: #1f2937;
  }
  table { border-collapse: collapse; margin: 8px 0; width: 100%; font-size: 14px; }
  th { background: #1e40af; color: #ffffff; padding: 7px 10px; border: 1px solid #1e3a8a; text-align: center; }
  td { padding: 7px 10px; border: 1px solid #cbd5e1; background: #ffffff; }
  tr:nth-child(even) td { background: #f1f5f9; }
  .tip {
    background: #fef3c7;
    border-left: 5px solid #f59e0b;
    padding: 7px 14px;
    margin: 8px 0;
    border-radius: 0 8px 8px 0;
    font-size: 13px;
    color: #7c2d12;
  }
  .recommend {
    background: #ecfdf5;
    border: 2px solid #10b981;
    padding: 10px 18px;
    margin: 8px 0;
    border-radius: 10px;
    font-size: 14px;
  }
  .ng {
    background: #fef2f2;
    border-left: 5px solid #dc2626;
    padding: 10px 16px;
    margin: 8px 0;
    border-radius: 0 8px 8px 0;
    color: #7f1d1d;
    font-size: 14px;
  }
  .ok {
    background: #ecfdf5;
    border-left: 5px solid #10b981;
    padding: 7px 14px;
    margin: 8px 0;
    border-radius: 0 8px 8px 0;
    font-size: 13px;
    color: #065f46;
  }
  .magnet {
    background: #fffbeb;
    border: 3px dashed #f59e0b;
    padding: 18px 24px;
    margin: 12px 0;
    border-radius: 12px;
    font-size: 18px;
    color: #78350f;
    line-height: 2;
  }
  .q-card {
    background: #f8faff;
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 12px 18px;
    margin: 8px 0;
    font-size: 14px;
  }
  .q-card h3 { color: #1e40af; margin-top: 0; }
  .star-row {
    background: #fffbeb;
    border: 2px solid #f59e0b;
    border-radius: 8px;
    padding: 10px 16px;
    margin: 6px 0;
    font-size: 14px;
    color: #78350f;
  }
  .flow {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-radius: 10px;
    padding: 12px 20px;
    margin: 8px 0;
    font-size: 14px;
    line-height: 1.9;
  }
  .sep { border: none; border-top: 2px dashed #93c5fd; margin: 10px 0; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  ul, ol { font-size: 15px; line-height: 1.7; margin: 4px 0; }
  li { margin-bottom: 3px; }
  header { color: #64748b; font-size: 13px; }
  footer { color: #64748b; font-size: 12px; }
---

<!--
=============================================================
  面接対策スライド Marp テンプレート（2026-05 確定版）
  このファイルの frontmatter（---〜---）を各スライドの
  先頭にそのままコピーして使う。
  {{...}} のプレースホルダーを実際の値に置換すること。

  置換表：
    {{SLIDE_TITLE}}      → 例: 想定問答集
    {{COMPANY_NAME}}     → 例: 府中ハローワーク
    {{APPLICANT_NAME}}   → 例: 渡邉 珠美
    {{INTERVIEW_DATE}}   → 例: 2026.05.12
    {{JOB_TITLE}}        → 例: 求人者支援員・生涯現役支援窓口
=============================================================
-->

<!-- ========================================================
  スライドクラス一覧（使い方リファレンス）
  ======================================================== -->

<!-- _class: title -->

# {{SLIDE_TITLE}}

## {{COMPANY_NAME}} 面接対策

**応募者：{{APPLICANT_NAME}}**
面接日：{{INTERVIEW_DATE}}
{{JOB_TITLE}}

---

<!-- _class: core -->
<!-- 使用場面: 02_自己PR案 のコアフレーズ強調スライド -->

# 🗝️ 自己PRの核（必ず最初と最後で言う）

<div class="bigbox">

（コアフレーズをここに書く）

</div>

---

<!-- _class: hero -->
<!-- 使用場面: 重要情報ハイライト（03逆質問の鉄板セット、04のアクセス情報 等） -->

# 📍 重要情報タイトル

## サブタイトル

<div class="star-box">

⭐ 第一選択：...
⭐ 第二選択：...

</div>

---

<!-- _class: mantra -->
<!-- 使用場面: 04_事前準備チェックリスト の末尾「面接直前の心の呪文」 -->

# 🧘 面接直前の心の呪文

<div class="mantra-box">

① 　（ここに心構えを書く）

② 　（ここに心構えを書く）

</div>

---

<!-- ========================================================
  通常スライドのパーツ例（クラスなし = 白背景）
  ======================================================== -->

# 見出しサンプル（h1）

## セクション見出し（h2）

### 小見出し（h3）

通常テキスト。**strong は赤太字**。

> blockquote は青ボーダー＋水色背景。面接回答の本文に使う。

<div class="tip">💡 tipボックス：黄色背景。ヒント・注意事項。</div>

<div class="recommend">🏆 recommendボックス：緑枠。推奨・ベストチョイス。</div>

<div class="ng">⚠️ ngボックス：赤ボーダー。NG表現・絶対禁止事項。</div>

<div class="ok">✅ okボックス：緑ボーダー。OKパターン・正解例。</div>

<div class="magnet">★ magnetボックス：黄破線枠。磁力ワード一覧。</div>

<div class="sep"></div>

<div class="two-col">
<div>

左カラム（two-col）

</div>
<div>

右カラム（two-col）

</div>
</div>

---

<!-- q-card: 03_逆質問集 の各質問カードに使う -->

<div class="q-card">

### ⭐ Q1.【★★★最推奨】質問タイトル

> 質問本文をここに書く

**狙い** ：面接官に与えたい印象・引き出したい情報。

</div>

---

<!-- flow: 04_事前準備チェックリスト の入退室フローに使う -->

<div class="flow">

① ドアの前で一呼吸
↓　② ノック3回
↓　③ 「どうぞ」の声を待つ
↓　④ 「失礼いたします」と入室

</div>
