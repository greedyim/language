# Scaling Plan

Phraseflow should grow from the bundled MVP deck into a large card system that can handle collocations, n-grams, and fixed phrases without forcing everything into one JavaScript file. Ordinary words should be learned through the collocations they appear in, not as isolated front-side cards.

## Card Shape

The front side should always be a real phrase or collocation. A card can still teach one or more target words by marking the important words in the metadata.

```json
{
  "id": "en-collocation-make-a-decision",
  "kind": "collocation",
  "text": "make a decision",
  "targetWords": [
    { "lemma": "make", "role": "verb" },
    { "lemma": "decision", "role": "noun" }
  ],
  "meaning": "決定する",
  "note": "make は「作る」だけでなく、decision などの抽象名詞と結びついて「行う/下す」の意味になる。",
  "examples": [
    {
      "en": "We need to make a decision today.",
      "ja": "今日、決定する必要があります。"
    }
  ],
  "frequency": {
    "rank": 84,
    "count": 123456,
    "source": "corpus-name"
  }
}
```

`kind` can be `collocation`, `ngram`, `phrase`, or `idiom`. The app should avoid `kind: "word"` as a learning card type. If a learner needs to learn `make`, the deck should include several cards such as `make a decision`, `make sense`, and `make sure`, then connect those cards through `targetWords`.

## Storage

The MVP uses `phrases.js` and `localStorage`. That is fine for a few hundred cards, but not for tens of thousands of words and hundreds of thousands of phrases.

The public version should use:

- Chunked static JSON files by frequency band, CEFR level, topic, and card kind
- A small manifest file that lists available deck chunks and versions
- IndexedDB for downloaded cards, review state, and local search indexes
- A service worker cache for the current active deck only
- `localStorage` only for lightweight settings

## Scheduling

Review records should remain separate from card content:

```json
{
  "cardId": "en-ngram-as-well-as",
  "status": "review",
  "seen": 4,
  "known": 2,
  "review": 2,
  "streak": 1,
  "ease": 2.3,
  "dueAt": 1781100000000,
  "updatedAt": 1781000000000
}
```

This lets the app update corpus data without losing a learner's history.

## Data Pipeline

1. Import corpus frequency files and dictionary/collocation sources.
2. Normalize spellings, contractions, punctuation, and case.
3. Score candidates by frequency, usefulness, ambiguity reduction, and learnability.
4. Generate cards with stable IDs and short examples.
5. Publish versioned deck chunks as static assets.

The important product rule is that the prompt should be the usage unit. A single word should not stand alone; it should be learned through collocations that disambiguate it in real use.
