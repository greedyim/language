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
  id: "ng-00001-of-the",
  kind: "ngram",
  text: "of the",
  meaning: "高頻度の読解チャンク",
  targetWords: [{ lemma: "of" }, { lemma: "the" }],
  gram: 2,
  rank: 1,
  sourceRank: 1,
  freq: 1746034516
}
```

`gram`、`rank`、`sourceRank`、`freq` は、Google Books Ngram Corpus v3から作られた公開n-gram頻度リストをもとにしています。まずは英語全体コーパスの高頻度2〜5-gramを優先し、出版物の権利文言など読解学習に向かない機械的ノイズを除外した不足分をEnglish Fictionの高頻度リストで補っています。

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
