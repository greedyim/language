from __future__ import annotations

import csv
import json
import re
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "core-10000"
CHUNK_SIZE = 1000
TARGET_COUNT = 10_000

BASE_URL = "https://raw.githubusercontent.com/orgtre/google-books-ngram-frequency/main/ngrams"
SOURCE_FILES = [
    ("english", 2),
    ("english", 3),
    ("english", 4),
    ("english", 5),
    ("english-fiction", 2),
    ("english-fiction", 3),
    ("english-fiction", 4),
    ("english-fiction", 5),
]

SOURCE_LABELS = {
    "english": "Google Books Ngram v3 / English 2010-2019",
    "english-fiction": "Google Books Ngram v3 / English Fiction 2010-2019",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "his",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "may",
    "might",
    "not",
    "of",
    "on",
    "or",
    "our",
    "she",
    "should",
    "that",
    "the",
    "their",
    "there",
    "they",
    "this",
    "to",
    "was",
    "we",
    "were",
    "will",
    "with",
    "would",
    "you",
    "your",
}

REJECT_PATTERNS = [
    "all rights reserved",
    "be copied",
    "cengage",
    "content may be suppressed",
    "copied",
    "deemed that any suppressed",
    "duplicated",
    "ebook",
    "electronic rights",
    "editorial review",
    "for additional information",
    "halseth",
    "intentionally left blank",
    "learning reserves",
    "materially affect",
    "may not be copied",
    "parallel bible",
    "party content may be",
    "published their study",
    "rights restrictions",
    "scanned",
    "subsequent rights",
    "suppressed content",
    "suppressed from",
    "third party content",
]

CONTRACTIONS = [
    (r"\bI 'm\b", "I'm"),
    (r"\bI 'd\b", "I'd"),
    (r"\bI 'll\b", "I'll"),
    (r"\bI 've\b", "I've"),
    (r"\bit 's\b", "it's"),
    (r"\bthat 's\b", "that's"),
    (r"\bthere 's\b", "there's"),
    (r"\bwhat 's\b", "what's"),
    (r"\byou 're\b", "you're"),
    (r"\byou 've\b", "you've"),
    (r"\bwe 're\b", "we're"),
    (r"\bthey 're\b", "they're"),
    (r"\bhe 's\b", "he's"),
    (r"\bshe 's\b", "she's"),
    (r"\bcan not\b", "cannot"),
]


@dataclass(frozen=True)
class Candidate:
    text: str
    corpus_text: str
    gram: int
    source_key: str
    source_rank: int
    freq: int


def fetch_csv(source_key: str, gram: int) -> list[dict[str, str]]:
    url = f"{BASE_URL}/{gram}grams_{source_key}.csv"
    with urllib.request.urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8")
    return list(csv.DictReader(text.splitlines()))


def normalize_text(text: str) -> str:
    value = text.strip()
    value = re.sub(r"\s+,", ",", value)
    value = re.sub(r"\s+", " ", value)
    for pattern, replacement in CONTRACTIONS:
        value = re.sub(pattern, replacement, value)
    if value and value[0].islower() and re.match(r"^(i|i'm|i'd|i'll|i've)\b", value, re.I):
        value = value[0].upper() + value[1:]
    return value


def slugify(text: str) -> str:
    value = text.lower().replace("'", "")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:80] or "ngram"


def tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text.lower())


def reject(text: str) -> bool:
    lowered = text.lower()
    if any(pattern in lowered for pattern in REJECT_PATTERNS):
        return True
    if re.search(r"\b[a-z]+@[a-z]+", lowered):
        return True
    if len(tokens(text)) < 2:
        return True
    return False


def target_words(text: str) -> list[dict[str, str]]:
    words = [word for word in tokens(text) if word not in STOPWORDS]
    if not words:
        words = tokens(text)
    unique: list[str] = []
    for word in words:
        if word not in unique:
            unique.append(word)
    return [{"lemma": word} for word in unique[:4]]


def tags_for(text: str, gram: int) -> list[str]:
    lowered = text.lower()
    tags = [f"{gram}-gram"]
    if any(word in lowered.split() for word in ("not", "cannot", "no", "never")):
        tags.append("negative")
    if any(word in lowered.split() for word in ("if", "when", "because", "while")):
        tags.append("connector")
    if any(word in lowered.split() for word in ("can", "could", "may", "might", "would", "should", "will")):
        tags.append("modal")
    if any(word in lowered.split() for word in ("of", "in", "on", "at", "from", "with", "to")):
        tags.append("structure")
    return tags[:4]


def make_card(candidate: Candidate, overall_rank: int) -> dict[str, object]:
    focus = target_words(candidate.text)
    focus_text = " / ".join(item["lemma"] for item in focus)
    return {
        "id": f"ng-{overall_rank:05d}-{slugify(candidate.text)}",
        "kind": "ngram",
        "text": candidate.text,
        "corpusText": candidate.corpus_text,
        "meaning": "高頻度の読解チャンク",
        "note": f"対象語: {focus_text}。単語単体ではなく、この並びを見た瞬間にひとかたまりで処理する。",
        "example": f'Read "{candidate.text}" as one unit.',
        "exampleJa": f"「{candidate.text}」を語順ごと覚える。",
        "gram": candidate.gram,
        "rank": overall_rank,
        "sourceRank": candidate.source_rank,
        "freq": candidate.freq,
        "source": SOURCE_LABELS[candidate.source_key],
        "sourceList": candidate.source_key,
        "tags": tags_for(candidate.text, candidate.gram),
        "targetWords": focus,
    }


def load_candidates() -> tuple[list[Candidate], dict[str, int]]:
    candidates: list[Candidate] = []
    raw_counts: dict[str, int] = {}
    for source_key, gram in SOURCE_FILES:
        rows = fetch_csv(source_key, gram)
        raw_counts[f"{source_key}-{gram}"] = len(rows)
        for index, row in enumerate(rows, start=1):
            corpus_text = row["ngram"]
            text = normalize_text(corpus_text)
            candidates.append(
                Candidate(
                    text=text,
                    corpus_text=corpus_text,
                    gram=gram,
                    source_key=source_key,
                    source_rank=index,
                    freq=int(row["freq"]),
                )
            )
    return candidates, raw_counts


def source_priority(candidate: Candidate) -> tuple[int, int, int, int]:
    source_order = 0 if candidate.source_key == "english" else 1
    gram_order = {2: 0, 3: 1, 4: 2, 5: 3}[candidate.gram]
    return (source_order, gram_order, candidate.source_rank, -candidate.freq)


def build_deck() -> dict[str, object]:
    candidates, raw_counts = load_candidates()
    selected: list[Candidate] = []
    seen: set[str] = set()
    rejected = 0

    for candidate in sorted(candidates, key=source_priority):
        key = candidate.text.lower()
        if key in seen:
            continue
        if reject(candidate.text):
            rejected += 1
            continue
        seen.add(key)
        selected.append(candidate)
        if len(selected) == TARGET_COUNT:
            break

    if len(selected) != TARGET_COUNT:
        raise RuntimeError(f"Expected {TARGET_COUNT} cards, got {len(selected)}")

    cards = [make_card(candidate, index) for index, candidate in enumerate(selected, start=1)]
    selected_by_source = Counter(card["sourceList"] for card in cards)
    selected_by_gram = Counter(str(card["gram"]) for card in cards)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    chunks = []
    for chunk_index in range(0, len(cards), CHUNK_SIZE):
        chunk_cards = cards[chunk_index : chunk_index + CHUNK_SIZE]
        name = f"chunk-{chunk_index // CHUNK_SIZE + 1:02d}.json"
        path = OUT_DIR / name
        path.write_text(
            json.dumps(chunk_cards, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
            newline="\n",
        )
        chunks.append({"file": name, "count": len(chunk_cards)})

    manifest = {
        "id": "core-10000",
        "title": "Core 10,000",
        "version": 1,
        "description": "High-frequency English n-gram and collocation cards for reading coverage.",
        "source": "orgtre/google-books-ngram-frequency, Google Books Ngram Corpus v3 20200217",
        "sourceUrl": "https://github.com/orgtre/google-books-ngram-frequency",
        "license": "Creative Commons Attribution 3.0 Unported, as stated by source repository",
        "total": len(cards),
        "chunkSize": CHUNK_SIZE,
        "chunks": chunks,
        "stats": {
            "rawCounts": raw_counts,
            "selectedBySource": dict(sorted(selected_by_source.items())),
            "selectedByGram": dict(sorted(selected_by_gram.items())),
            "rejectedByQualityFilter": rejected,
            "sourceLists": SOURCE_LABELS,
        },
    }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


if __name__ == "__main__":
    print(json.dumps(build_deck(), ensure_ascii=False, indent=2))
