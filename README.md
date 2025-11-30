# LP信頼診断エージェント v0（PoC）

「短期CVRだけ盛るLP」ではなく、**信頼・ブランド価値を守りながら売れるLPか？** を診断するための PoC 実装です。

- 対象：ランディングページ（LP）
- 出力：3レイヤー × 6軸（全軸 1〜5 点）＋コメント
- 実装レベル：ローカルスクリプトで 1LP = 1コマンド診断できる v0

> ⚠️ 注意  
> 実LPのHTMLやテスト用データ（商用サイトのコピー）は、このリポジトリには含めません。  
> 手元でテストする場合は、`samples/` 以下に **自分の責任で取得したHTML** を置いてください

---

## 1. プロジェクト構成（想定）

```text
lp-trust-diagnoser/
  README.md
  .gitignore
  requirements.txt
  .env.example      # APIキー名だけ定義するサンプル（値は空）
  diagnose_lp.py    # コマンドラインからLPを診断するスクリプト
  lp_trust_diagnoser/
    __init__.py
    ingestion/
      __init__.py
      html_loader.py      # HTML→テキスト・セクション抽出
    llm/
      __init__.py
      gemini_client.py    # Gemini API クライアント
    prompts/
      __init__.py
      scan_and_coach_ja.py  # Scan & Coach 用 System プロンプト
  samples/             # テスト用LP（git管理外）
    (ローカルだけで使うHTMLファイル)
  logs/                # 実行ログ・診断結果JSONなど（git管理外）
````

※実際の構成が多少違っていても OK です。
　最低限、`diagnose_lp.py` と `lp_trust_diagnoser/` パッケージがあれば動作します。

---

## 2. セットアップ

### 2-1. 前提

* Python 3.11 以上（3.12 でも可）
* Git
* Gemini API キー（[Google AI Studio](https://aistudio.google.com/) から取得）

### 2-2. 仮想環境の作成

Windows（PowerShell）の例：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
```

macOS / Linux の例：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2-3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

---

## 3. APIキーの設定

### 3-1. `.env` ファイル

リポジトリルートに `.env` を作成し、GeminiのAPIキーを設定します。

```dotenv
GEMINI_API_KEY=ここにあなたのAPIキー
# または
# GOOGLE_API_KEY=ここにあなたのAPIキー
```

---

## 4. 使い方（LP診断）

### 4-1. 手元でテスト用LPを準備

1. ブラウザで診断したいLPを開く
2. 「ページのHTMLを保存」などで `.html` ファイルとして保存
3. このリポジトリの `samples/` ディレクトリに置く
   （例：`samples/sample_lp_a.html`）

> ⚠️ テストに使うLPは、このリポジトリにはコミットしません。
> 商用サイトのHTMLを扱う場合は、各自の責任で法的・倫理的に問題ない範囲でご利用ください。

### 4-2. コマンド例

プレーンなJSON出力：

```bash
python diagnose_lp.py samples/sample_lp_a.html
```

整形表示（`--pretty` オプションがある場合）：

```bash
python diagnose_lp.py samples/sample_lp_a.html --pretty
```

想定するJSON出力イメージ：

```json
{
  "axes": {
    "trust_transparency": {
      "score": 3,
      "reason": "会社名と問い合わせ窓口は明記されているが、所在地や代表者情報はLPからは分からない。",
      "improvement_hint": "会社概要への導線をLP内の分かりやすい場所に追加すると、信頼性が高まる。"
    },
    "...": {}
  },
  "summary_comment": "..."
}
```

---

## 5. 仕組みの概要

### 5-1. ingestion（HTML → セクションテキスト）

* BeautifulSoupでタグを削りつつテキスト抽出
* キーワード・簡易ルールで、

  * hero（冒頭）
  * pricing（料金・キャンペーン周り）
  * cancel（解約・返品・休止など）
  * reviews（事例・レビュー）
    にざっくり分割
* v0 なので「人間の流し読みレベル」の粗さを許容

### 5-2. Scan & Coach（6軸診断）

* `SCAN_AND_COACH_SYSTEM_PROMPT_JA` に、3レイヤー×6軸＋スコア定義を記述
* User入力には `hero/pricing/cancel/reviews/raw` の要約テキストを渡し、
  LLMに 6軸分の:

  * `score`（1〜5）
  * `reason`
  * `improvement_hint`
    と、全体の `summary_comment` を返させる。

---

## 6. 今後の拡張予定（メモ）

* FastAPI で `/diagnose` エンドポイントを生やして簡易API化
* `diagnosis_logs` テーブル（SQLite）を追加し、LPごとの診断ログを蓄積
* 5〜10枚のLPで人間ラベル vs LLMスコアの差分を集計し、
  軸ごとのバイアス（甘い・厳しい）の可視化
* クライアント別の重み付け＆Human-in-the-loop付きの改善ループ実装

---

## 7. ライセンス / 注意事項

* このリポジトリは PoC 用です。本番運用前提ではありません。
* 商用LPのHTMLを保存・分析する場合は、各自の責任で法的・倫理的な問題がないように運用してください。
* Gemini API の利用規約・料金体系は、公式ドキュメントを確認してください。

````
