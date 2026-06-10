# Phraseflow

iPhoneで片手操作しやすい、スワイプ式の英語コロケーション暗記Webアプリです。単語単体ではなく、Google Books Ngram Corpus由来の高頻度n-gramやコロケーションを学習カードとして扱います。

## MVP

- タップで意味、ニュアンス、例文を表示
- 右スワイプまたは右下ボタンで「覚えた」
- 左スワイプまたは左下ボタンで「復習」
- 進捗はブラウザのlocalStorageに保存
- 復習、新規、全体のデッキ切り替え
- 学習履歴のJSONエクスポートとインポート
- カードのピンチ拡大、またはカード内アイコンで全画面表示
- Google Books Ngram由来の高頻度カード10,000問
- 低品質な機能語断片や出版ノイズを除外し、core/supportの2層で並び替え
- 例文は手作業で書いたカードだけ表示
- PWA用manifestとservice worker

## 使い方

静的ファイルだけで動くため、任意の静的ホスティングに配置できます。大規模デッキはJSONをfetchするため、ローカルではHTTPサーバー経由で開きます。

ローカル確認:

```powershell
python -m http.server 4173
```

その後 `http://localhost:4173` を開きます。

## データ

メインデッキは `data/core-10000/` にあります。10チャンクに分けたJSONを起動時に読み込みます。`phrases.js` は読み込み失敗時の小さなフォールバックデッキです。

各カードは以下のような構造です。

```js
{
  id: "ng-00001-one-of-the",
  kind: "ngram",
  text: "one of the",
  readingType: "部分表現",
  meaning: "複数の中の一つ: one of the + 最上級/複数名詞",
  note: "後ろに集合が来る。oneを単独で訳さず、全体から一つを取り出す形で読む。",
  example: "This is one of the phrases worth learning first.",
  exampleJa: "これは最初に覚える価値があるフレーズの一つだ。",
  exampleStatus: "manual",
  qualityTier: "core",
  targetWords: [{ lemma: "one" }],
  gram: 3,
  rank: 1,
  sourceRank: 1,
  freq: 66464125
}
```

`gram`、`rank`、`sourceRank`、`freq` は、Google Books Ngram Corpus v3から作られた公開n-gram頻度リストをもとにしています。まずは英語全体コーパスの高頻度2〜5-gramを優先し、出版物の権利文言、短すぎる機能語断片、途中で切れたような低品質候補を除外します。厳密フィルタを通った `core` を先に並べ、10,000問を維持するために読解パターンとして使える候補だけを `support` として後ろに補っています。例文は `exampleStatus: "manual"` のカードだけに表示します。

再生成:

```powershell
python scripts/build_ngram_deck.py
```

出典:

- orgtre/google-books-ngram-frequency: https://github.com/orgtre/google-books-ngram-frequency
- Google Books Ngram Corpus v3: https://storage.googleapis.com/books/ngrams/books/datasetsv3.html

## 公開

公開URL:

```text
https://greedyim.github.io/language/
```

## 次の拡張

- 数万単語、数十万フレーズを扱うためのIndexedDB保存
- CSV/JSONからデッキを差し替えられる管理画面
- CEFRや用途別タグの追加
- SupabaseやFirebaseによる任意ログイン同期
- 一般公開向けの利用規約、プライバシーポリシー、データ出典ページ

大規模化の方針は `docs/scaling.md` にまとめています。
