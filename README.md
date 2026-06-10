# Phraseflow

iPhoneで片手操作しやすい、スワイプ式の英語フレーズ暗記Webアプリです。単語単体ではなく、Google Books Ngram Corpus由来の高頻度n-gramや定型フレーズを学習カードとして扱います。

## MVP

- タップで意味、ニュアンス、例文を表示
- 右スワイプまたは右下ボタンで「覚えた」
- 左スワイプまたは左下ボタンで「復習」
- 進捗はブラウザのlocalStorageに保存
- 復習、新規、全体のデッキ切り替え
- 学習履歴のJSONエクスポートとインポート
- カードのピンチ拡大、またはカード内アイコンで全画面表示
- PWA用manifestとservice worker

## 使い方

静的ファイルだけで動くため、`index.html`を開くか、任意の静的ホスティングに配置できます。

ローカル確認:

```powershell
python -m http.server 4173
```

その後 `http://localhost:4173` を開きます。

## データ

初期デッキは `phrases.js` にあります。各カードは以下のような構造です。

```js
{
  id: "p001",
  text: "as well as",
  meaning: "...だけでなく...も",
  gram: 3,
  rank: 3,
  freq: 52977493
}
```

`gram`、`rank`、`freq` は、Google Books Ngram Corpus v3から作られた公開n-gram頻度リストをもとにしています。MVPでは上位n-gramから学習単位として自然なものを手動選定し、日本語の意味と例文を付与しています。

出典:

- orgtre/google-books-ngram-frequency: https://github.com/orgtre/google-books-ngram-frequency
- Google Books Ngram Corpus v3: https://storage.googleapis.com/books/ngrams/books/datasetsv3.html

## 公開

GitHub Pagesで公開する場合は、このリポジトリの `main` ブランチ直下をPagesのソースに指定します。

公開URL:

```text
https://greedyim.github.io/language/
```

## 次の拡張

- 単語単体ではなく、対象語を含むコロケーションカードで語彙を覚えられるようにする
- 数万単語、数十万フレーズを扱うためのチャンク化JSONとIndexedDB保存
- CSV/JSONからデッキを差し替えられる管理画面
- CEFRや用途別タグの追加
- SupabaseやFirebaseによる任意ログイン同期
- 一般公開向けの利用規約、プライバシーポリシー、データ出典ページ

大規模化の方針は `docs/scaling.md` にまとめています。
