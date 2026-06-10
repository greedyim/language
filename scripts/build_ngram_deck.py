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
GRAM_TARGETS = {2: 2500, 3: 3500, 4: 2500, 5: 1500}

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

ARTICLES = {"a", "an", "the"}
DETERMINERS = ARTICLES | {
    "all",
    "another",
    "any",
    "each",
    "every",
    "few",
    "her",
    "his",
    "its",
    "many",
    "more",
    "most",
    "my",
    "no",
    "our",
    "other",
    "several",
    "some",
    "such",
    "that",
    "their",
    "these",
    "this",
    "those",
    "your",
}
PREPOSITIONS = {
    "about",
    "above",
    "across",
    "after",
    "against",
    "along",
    "among",
    "around",
    "as",
    "at",
    "before",
    "behind",
    "between",
    "by",
    "during",
    "for",
    "from",
    "in",
    "inside",
    "into",
    "near",
    "of",
    "off",
    "on",
    "onto",
    "over",
    "through",
    "to",
    "under",
    "until",
    "with",
    "within",
    "without",
}
CONNECTORS = {"although", "because", "if", "since", "though", "unless", "when", "where", "while"}
COORDINATORS = {"and", "but", "or", "nor", "yet"}
PRONOUNS = {
    "he",
    "her",
    "hers",
    "him",
    "his",
    "i",
    "it",
    "its",
    "me",
    "mine",
    "my",
    "our",
    "ours",
    "she",
    "their",
    "theirs",
    "them",
    "they",
    "us",
    "we",
    "you",
    "your",
    "yours",
}
BE_FORMS = {"am", "are", "be", "been", "being", "is", "was", "were"}
HAVE_FORMS = {"had", "has", "have", "having"}
DO_FORMS = {"did", "do", "does", "doing"}
MODALS = {"can", "cannot", "could", "may", "might", "must", "shall", "should", "will", "would"}
NEGATIVES = {"never", "no", "not"}
AUXILIARY_CONTRACTIONS = {
    "can't",
    "couldn't",
    "didn't",
    "doesn't",
    "don't",
    "hadn't",
    "hasn't",
    "haven't",
    "he's",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "isn't",
    "it's",
    "she's",
    "that's",
    "there's",
    "they're",
    "wasn't",
    "we're",
    "weren't",
    "won't",
    "wouldn't",
    "you're",
}
BASE_VERBS = {
    "add",
    "allow",
    "ask",
    "be",
    "become",
    "bring",
    "build",
    "call",
    "change",
    "check",
    "come",
    "create",
    "do",
    "find",
    "follow",
    "get",
    "give",
    "go",
    "have",
    "help",
    "include",
    "keep",
    "know",
    "learn",
    "leave",
    "look",
    "make",
    "move",
    "need",
    "put",
    "read",
    "remain",
    "remember",
    "run",
    "say",
    "see",
    "set",
    "show",
    "take",
    "talk",
    "try",
    "turn",
    "understand",
    "use",
    "work",
    "write",
}
ADJECTIVE_ENDINGS = {
    "able",
    "available",
    "better",
    "best",
    "clear",
    "different",
    "early",
    "first",
    "full",
    "good",
    "great",
    "high",
    "important",
    "large",
    "last",
    "local",
    "long",
    "low",
    "main",
    "major",
    "new",
    "next",
    "old",
    "only",
    "other",
    "possible",
    "present",
    "public",
    "right",
    "same",
    "second",
    "short",
    "small",
    "social",
    "special",
    "sure",
    "true",
    "whole",
}


@dataclass(frozen=True)
class CardCopy:
    reading_type: str
    meaning: str
    note: str
    example: str | None = None
    example_ja: str | None = None


FUNCTION_WORDS = (
    STOPWORDS
    | DETERMINERS
    | PREPOSITIONS
    | CONNECTORS
    | COORDINATORS
    | PRONOUNS
    | BE_FORMS
    | HAVE_FORMS
    | DO_FORMS
    | MODALS
    | NEGATIVES
    | AUXILIARY_CONTRACTIONS
)
LOW_VALUE_EXACT = {
    "all the",
    "and a",
    "and he",
    "and i",
    "and that",
    "and the",
    "are not",
    "as he",
    "as the",
    "at the",
    "be a",
    "but i",
    "but the",
    "by a",
    "by the",
    "can be",
    "could not",
    "did not",
    "do not",
    "does not",
    "for a",
    "for the",
    "from the",
    "had been",
    "has been",
    "have been",
    "he had",
    "he was",
    "i am",
    "i can",
    "i do",
    "i had",
    "i have",
    "i was",
    "if the",
    "if you",
    "in a",
    "in his",
    "in the",
    "in this",
    "is a",
    "is not",
    "is the",
    "it is",
    "it was",
    "may be",
    "not be",
    "of a",
    "of her",
    "of his",
    "of the",
    "of their",
    "of these",
    "of this",
    "on a",
    "on the",
    "she had",
    "she was",
    "that he",
    "that i",
    "that is",
    "that it",
    "that the",
    "there are",
    "there is",
    "there was",
    "they are",
    "they were",
    "this is",
    "to a",
    "to be",
    "to the",
    "was a",
    "was not",
    "was the",
    "will be",
    "with a",
    "with the",
    "would be",
    "you are",
    "you can",
}
UTILITY_COPIES = {
    "a few": CardCopy(
        "数量表現",
        "少数をまとめて読む: a few + 複数名詞",
        "fewだけだと「ほとんどない」に寄りやすいが、a fewは「少しある」と前向きに読む。",
        "A few people stayed after the meeting.",
        "会議のあと、数人が残った。",
    ),
    "a lot": CardCopy(
        "数量表現",
        "まとまった量: a lot / a lot of",
        "後ろにofが来ると名詞の量を表し、単独では程度を強める。",
        "The team learned a lot from the first test.",
        "チームは最初のテストから多くを学んだ。",
    ),
    "a lot of": CardCopy(
        "数量表現",
        "多量の: a lot of + 名詞",
        "ofの後ろに数えられる名詞も数えられない名詞も置ける。",
        "A lot of people noticed the change.",
        "多くの人がその変化に気づいた。",
    ),
    "able to": CardCopy(
        "可能表現",
        "できる状態: be able to + 動詞",
        "canより少し説明的で、能力や条件が整っていることを表す。",
        "She was able to explain the result clearly.",
        "彼女は結果を明確に説明できた。",
    ),
    "according to": CardCopy(
        "出典表現",
        "情報源を示す: according to + 情報源",
        "主張の責任を、後ろに来る資料・人物・規則へつなぐ。",
        "According to the report, the number is rising.",
        "その報告によると、数値は上がっている。",
    ),
    "as a result": CardCopy(
        "結果表現",
        "その結果: 前の内容を結果へつなぐ",
        "文頭や文中で、原因から結果への流れを示す。",
        "As a result, the project finished earlier.",
        "その結果、プロジェクトは早く終わった。",
    ),
    "as if": CardCopy(
        "仮定表現",
        "まるで...のように: as if + 文",
        "実際とは限らない見え方や感じ方を導く。",
        "He spoke as if he knew the answer.",
        "彼は答えを知っているかのように話した。",
    ),
    "as long as": CardCopy(
        "条件表現",
        "...する限り: 条件の範囲を決める",
        "必要条件を丸ごと導くチャンクとして読む。",
        "You can stay as long as you need.",
        "必要なだけいていい。",
    ),
    "as soon as": CardCopy(
        "時間表現",
        "...するとすぐに: as soon as + 文",
        "出来事の直後に次の出来事が起きる流れを作る。",
        "Call me as soon as you arrive.",
        "着いたらすぐ電話して。",
    ),
    "as well": CardCopy(
        "追加表現",
        "...もまた: 文末で情報を足す",
        "tooと近く、直前の内容にもう一つ同じ方向の情報を加える。",
        "The app works offline as well.",
        "そのアプリはオフラインでも動く。",
    ),
    "as well as": CardCopy(
        "追加表現",
        "AだけでなくBも: as well as + 名詞/動名詞",
        "andよりも、追加される情報を少し添える感じで読む。",
        "The course teaches phrases as well as grammar.",
        "その講座は文法だけでなくフレーズも教える。",
    ),
    "at least": CardCopy(
        "下限表現",
        "少なくとも: 最低ラインを示す",
        "数量や評価の下限を置いて、主張を控えめにする。",
        "Read at least one page every day.",
        "毎日少なくとも1ページ読む。",
    ),
    "at the same time": CardCopy(
        "対比表現",
        "同時に / とはいえ: 追加や対比へつなぐ",
        "時間の同時性だけでなく、別の観点を並べる時にも使う。",
        "The task is simple and, at the same time, important.",
        "その作業は単純で、同時に重要でもある。",
    ),
    "because of": CardCopy(
        "原因表現",
        "...が原因で: because of + 名詞",
        "because + 文ではなく、名詞を原因として受ける。",
        "The game stopped because of the rain.",
        "雨のため試合は止まった。",
    ),
    "due to": CardCopy(
        "原因表現",
        "...が原因で / ...による",
        "名詞句を受けて、原因や理由をやや硬めに示す。",
        "The delay was due to a network problem.",
        "遅れはネットワークの問題によるものだった。",
    ),
    "even if": CardCopy(
        "譲歩表現",
        "たとえ...でも: 条件を認めた上で主文へ進む",
        "条件が成り立っても結論は変わらない、という読みになる。",
        "Even if it rains, the event will continue.",
        "たとえ雨でも、イベントは続く。",
    ),
    "even though": CardCopy(
        "譲歩表現",
        "...にもかかわらず: 事実を認めて反対方向へ進む",
        "thoughより強く、意外性のある対比を作る。",
        "Even though it was late, she kept reading.",
        "遅い時間だったが、彼女は読み続けた。",
    ),
    "for example": CardCopy(
        "例示表現",
        "例えば: 直前の一般論に具体例を足す",
        "読む時は、ここから具体例が始まる合図として処理する。",
        "For example, this phrase appears in many books.",
        "例えば、このフレーズは多くの本に出てくる。",
    ),
    "going to": CardCopy(
        "予定表現",
        "...するつもり / ...しそう: be going to + 動詞",
        "未来の予定や、今の状況から見える成り行きを表す。",
        "They are going to change the schedule.",
        "彼らは予定を変更するつもりだ。",
    ),
    "have to": CardCopy(
        "必要表現",
        "...しなければならない: have to + 動詞",
        "外から来る必要性や状況上の義務として読む。",
        "We have to check the source first.",
        "まず出典を確認しなければならない。",
    ),
    "in addition": CardCopy(
        "追加表現",
        "さらに: 前の内容に情報を足す",
        "段落内で追加の根拠や条件へ進む合図になる。",
        "In addition, the tool saves your progress.",
        "さらに、そのツールは進捗を保存する。",
    ),
    "in addition to": CardCopy(
        "追加表現",
        "...に加えて: in addition to + 名詞",
        "後ろの名詞句を追加条件として受ける。",
        "In addition to grammar, learners need phrases.",
        "文法に加えて、学習者にはフレーズが必要だ。",
    ),
    "in fact": CardCopy(
        "強調表現",
        "実際には / それどころか: 事実で補強する",
        "前の内容を、より具体的または強い事実で支える。",
        "In fact, the phrase is more common than expected.",
        "実際、そのフレーズは予想より一般的だ。",
    ),
    "in order to": CardCopy(
        "目的表現",
        "...するために: in order to + 動詞",
        "目的をはっきり示す、少し硬めのto不定詞として読む。",
        "She reviewed the notes in order to understand the text.",
        "彼女は本文を理解するためにノートを見直した。",
    ),
    "instead of": CardCopy(
        "代替表現",
        "...の代わりに: instead of + 名詞/動名詞",
        "選ばなかったものを後ろに置き、実際の選択と対比する。",
        "Use the phrase instead of a single word.",
        "単語一つではなく、そのフレーズを使う。",
    ),
    "kind of": CardCopy(
        "分類表現",
        "ある種類の / ちょっと: kind of + 名詞・形容詞",
        "分類にも、会話で意味を弱める働きにもなる。",
        "This kind of pattern appears everywhere.",
        "この種の型はあちこちに出てくる。",
    ),
    "less than": CardCopy(
        "比較表現",
        "...未満 / ...より少ない",
        "数量や程度が基準を下回ることを示す。",
        "The task took less than an hour.",
        "その作業は1時間未満で終わった。",
    ),
    "more than": CardCopy(
        "比較表現",
        "...より多い / ...以上に",
        "数量だけでなく、期待や単なる意味を超える時にも使う。",
        "More than fifty people joined the class.",
        "50人を超える人が授業に参加した。",
    ),
    "no longer": CardCopy(
        "変化表現",
        "もはや...ない: 以前との違いを示す",
        "現在はその状態ではない、と時間差を含めて読む。",
        "The old rule is no longer useful.",
        "古い規則はもはや役に立たない。",
    ),
    "not only": CardCopy(
        "追加表現",
        "ただ...だけでなく: not only A but also B",
        "後ろにbut alsoが来やすい、追加の前振りとして読む。",
        "The method is not only fast but also clear.",
        "その方法は速いだけでなく明確でもある。",
    ),
    "number of": CardCopy(
        "数量表現",
        "数・多数: a number of / the number of",
        "a number ofは「いくつもの」、the number ofは「数そのもの」。",
        "A number of examples use the same pattern.",
        "いくつもの例が同じ型を使っている。",
    ),
    "on the other hand": CardCopy(
        "対比表現",
        "一方で: 反対側の観点へ移る",
        "議論の向きが変わる合図として読む。",
        "On the other hand, short phrases are easy to review.",
        "一方で、短いフレーズは復習しやすい。",
    ),
    "one of": CardCopy(
        "部分表現",
        "複数の中の一つ: one of + 複数名詞",
        "後ろには複数の集合が来る。oneを単独で訳さず、まとまりで読む。",
        "This is one of the most useful patterns.",
        "これは最も役に立つ型の一つだ。",
    ),
    "out of": CardCopy(
        "範囲表現",
        "...の中から / ...の外へ",
        "範囲・材料・出所から何かが出るイメージで読む。",
        "She chose three examples out of the list.",
        "彼女は一覧から3つの例を選んだ。",
    ),
    "part of": CardCopy(
        "部分表現",
        "...の一部: part of + 全体",
        "全体と部分の関係を作る基本チャンク。",
        "This phrase is part of a larger pattern.",
        "このフレーズはより大きな型の一部だ。",
    ),
    "rather than": CardCopy(
        "選択表現",
        "...ではなく: A rather than B",
        "選ぶものと選ばないものを対比する。",
        "Learn phrases rather than isolated words.",
        "孤立した単語ではなくフレーズを学ぶ。",
    ),
    "so that": CardCopy(
        "目的・結果表現",
        "...するように / その結果",
        "目的を示すことも、結果を示すこともある接続チャンク。",
        "Save the file so that you can review it later.",
        "あとで見直せるようにファイルを保存する。",
    ),
    "sort of": CardCopy(
        "分類表現",
        "一種の / ちょっと: sort of + 名詞・形容詞",
        "kind ofと同じく、分類にも意味を弱める働きにもなる。",
        "It is sort of a shortcut for reading.",
        "それは読解のための一種の近道だ。",
    ),
    "such as": CardCopy(
        "例示表現",
        "...など: such as + 例",
        "後ろに具体例が並ぶ合図。前の名詞を説明する。",
        "Read common chunks such as according to and as a result.",
        "according toやas a resultなどの共通チャンクを読む。",
    ),
    "used to": CardCopy(
        "過去習慣",
        "以前は...していた: used to + 動詞",
        "今は違う、という含みを持つ過去の習慣・状態。",
        "She used to read every sentence word by word.",
        "彼女は以前、一文ずつ単語単位で読んでいた。",
    ),
    "the same": CardCopy(
        "同一表現",
        "同じもの・同じ状態: the same",
        "後ろにasが続くと比較対象を示す。sameを単独で見ず、the sameで固定して読む。",
        "Two reports reached the same conclusion.",
        "二つの報告は同じ結論に達した。",
    ),
    "the first": CardCopy(
        "順序表現",
        "最初のもの・第一のもの: the first",
        "順序だけでなく、導入や優先順位を示す名詞句としてよく出る。",
        "The first step is to check the context.",
        "最初の手順は文脈を確認することだ。",
    ),
    "the other": CardCopy(
        "対比表現",
        "もう一方の / 他方の: the other",
        "二つあるうちの残り、または対比される側を指す。",
        "One answer was simple; the other was more precise.",
        "一つの答えは単純で、もう一方はより正確だった。",
    ),
    "the most": CardCopy(
        "最上級表現",
        "最も...: the most + 形容詞/副詞",
        "比較範囲の中で一番高い程度を示す合図として読む。",
        "This is the most common pattern in the list.",
        "これは一覧の中で最も一般的な型だ。",
    ),
    "the world": CardCopy(
        "名詞句",
        "世界・世の中: the world",
        "具体的な地球だけでなく、社会全体や人々のいる場としても読む。",
        "The world needs clearer information.",
        "世界にはより明確な情報が必要だ。",
    ),
    "new york": CardCopy(
        "固有名詞",
        "New York: 地名として一まとまりで読む",
        "二語を分けず、都市名・州名・組織名の一部として処理する。",
        "She moved to New York after college.",
        "彼女は大学卒業後ニューヨークへ移った。",
    ),
    "need to": CardCopy(
        "必要表現",
        "...する必要がある: need to + 動詞",
        "主語にとって必要な行動を後ろの動詞で受ける。",
        "You need to read the whole sentence.",
        "文全体を読む必要がある。",
    ),
    "want to": CardCopy(
        "希望表現",
        "...したい: want to + 動詞",
        "欲しいものではなく、したい行動が後ろに来る形として読む。",
        "I want to understand the article without translating every word.",
        "すべての語を訳さずにその記事を理解したい。",
    ),
    "try to": CardCopy(
        "試行表現",
        "...しようとする: try to + 動詞",
        "成功したかどうかより、行動を試みる方向を示す。",
        "Try to notice the phrase before each word.",
        "単語ごとに見る前に、そのフレーズに気づくようにしてみる。",
    ),
    "to make": CardCopy(
        "to不定詞",
        "作るために / 作ること: to make",
        "目的・結果・名詞の説明として、後ろの目的語まで受けて読む。",
        "She changed the layout to make the app easier to use.",
        "彼女はアプリを使いやすくするためにレイアウトを変えた。",
    ),
    "to get": CardCopy(
        "to不定詞",
        "得るために / 〜になるために: to get",
        "getの意味は文脈で変わるが、to getで目的や変化を導く。",
        "Read the paragraph again to get the main idea.",
        "要点をつかむためにその段落をもう一度読む。",
    ),
    "to see": CardCopy(
        "to不定詞",
        "見るために / 分かるために: to see",
        "実際に見るだけでなく、確認する・理解する意味にも広がる。",
        "Check the next sentence to see how the phrase works.",
        "そのフレーズがどう働くか確認するために次の文を見る。",
    ),
    "to do": CardCopy(
        "to不定詞",
        "すること / するために: to do",
        "doの中身は前後で決まるので、to doを行動の受け皿として読む。",
        "There is still a lot to do before release.",
        "公開前にまだやることがたくさんある。",
    ),
    "make sure": CardCopy(
        "確認表現",
        "必ず確認する: make sure + 文/that節",
        "後ろに来る内容が確実に成り立つよう確認する、という意味で読む。",
        "Make sure the card shows the whole phrase.",
        "カードにフレーズ全体が表示されることを確認する。",
    ),
    "make it": CardCopy(
        "達成表現",
        "間に合う / 成功する / それを作る: make it",
        "文脈で意味が変わるが、目標に届くイメージを持つことが多い。",
        "If we keep improving the deck, we can make it useful.",
        "デッキを改善し続ければ、役に立つものにできる。",
    ),
    "find out": CardCopy(
        "発見表現",
        "調べて分かる: find out",
        "偶然見るより、情報を得て判明する流れとして読む。",
        "Read the source to find out how often it appears.",
        "それがどれほど頻出するか知るために出典を読む。",
    ),
    "come from": CardCopy(
        "出所表現",
        "...に由来する / ...から来る: come from",
        "人・物・情報の起点を後ろに置く。",
        "These phrases come from a frequency list.",
        "これらのフレーズは頻度リストに由来する。",
    ),
    "look at": CardCopy(
        "視点表現",
        "...を見る / 検討する: look at",
        "物理的に見るだけでなく、データや問題を検討する意味でも使う。",
        "Look at the phrase before checking the meaning.",
        "意味を確認する前にそのフレーズを見る。",
    ),
    "look for": CardCopy(
        "探索表現",
        "...を探す: look for",
        "足りない情報や対象を探す方向を後ろの名詞で受ける。",
        "Look for the words that often appear together.",
        "一緒によく現れる語を探す。",
    ),
    "go through": CardCopy(
        "通過・確認表現",
        "一通り確認する / 通り抜ける: go through",
        "手順や資料を最初から最後まで進む意味でよく使う。",
        "Go through the review cards once a day.",
        "復習カードを一日一回通して確認する。",
    ),
    "based on": CardCopy(
        "根拠表現",
        "...に基づく: based on + 名詞",
        "判断・設計・説明の根拠を後ろの名詞で示す。",
        "The deck is based on high-frequency n-grams.",
        "そのデッキは高頻度n-gramに基づいている。",
    ),
    "related to": CardCopy(
        "関連表現",
        "...に関係している: related to + 名詞",
        "主題や原因とのつながりを後ろに置く。",
        "The note explains words related to the phrase.",
        "メモはそのフレーズに関連する語を説明している。",
    ),
    "similar to": CardCopy(
        "類似表現",
        "...に似ている: similar to + 名詞",
        "同じではないが近いものを、toの後ろに置く。",
        "This pattern is similar to the one above.",
        "この型は上のものに似ている。",
    ),
    "different from": CardCopy(
        "差異表現",
        "...とは違う: different from + 名詞",
        "比較対象をfromの後ろに置いて、差を示す。",
        "The phrase meaning is different from the word meaning.",
        "フレーズの意味は単語単体の意味とは違う。",
    ),
    "important to": CardCopy(
        "評価表現",
        "...にとって重要 / ...することが重要: important to",
        "toの後ろが人なら対象、動詞なら重要な行動として読む。",
        "It is important to review the same phrase again.",
        "同じフレーズをもう一度復習することが重要だ。",
    ),
    "likely to": CardCopy(
        "可能性表現",
        "...しそうだ: likely to + 動詞",
        "起こる可能性が高い行動や状態を後ろの動詞で受ける。",
        "Common phrases are likely to appear again.",
        "よく使われるフレーズはまた出てくる可能性が高い。",
    ),
    "at the end": CardCopy(
        "位置・時間表現",
        "最後に / 端で: at the end",
        "時間や場所の終点を示し、ofが続くと範囲が明確になる。",
        "The answer appears at the end of the sentence.",
        "答えは文の最後に現れる。",
    ),
    "in the end": CardCopy(
        "結果表現",
        "結局は / 最終的に: in the end",
        "いろいろあった後の結論や結果を示す。",
        "In the end, repeated exposure matters most.",
        "結局、繰り返し触れることが最も大事だ。",
    ),
    "in terms of": CardCopy(
        "観点表現",
        "...の観点では: in terms of + 名詞",
        "評価する軸や話題の範囲を後ろに置く。",
        "In terms of reading, phrases matter more than isolated words.",
        "読解の観点では、孤立した単語よりフレーズが重要だ。",
    ),
    "in front of": CardCopy(
        "位置表現",
        "...の前に: in front of + 名詞",
        "物理的な前だけでなく、人の前で起きる状況にも使う。",
        "She opened the app in front of the class.",
        "彼女はクラスの前でアプリを開いた。",
    ),
    "in the middle of": CardCopy(
        "位置・進行表現",
        "...の真ん中で / ...の最中に",
        "場所の中央にも、出来事が進行中であることにも使う。",
        "He stopped in the middle of the sentence.",
        "彼は文の途中で止まった。",
    ),
    "as part of": CardCopy(
        "部分表現",
        "...の一部として: as part of + 名詞",
        "活動・計画・全体の中に含まれるものとして読む。",
        "Use the deck as part of your daily reading practice.",
        "そのデッキを毎日の読解練習の一部として使う。",
    ),
    "as a result of": CardCopy(
        "原因結果表現",
        "...の結果として: as a result of + 名詞",
        "後ろに原因を置き、その結果起きたことへつなぐ。",
        "As a result of practice, the phrases felt familiar.",
        "練習の結果、そのフレーズは見慣れたものに感じられた。",
    ),
    "take care of": CardCopy(
        "処理・世話表現",
        "...の世話をする / ...に対処する: take care of",
        "人の世話にも、問題を片づける意味にも使う。",
        "The app will take care of the review list.",
        "そのアプリが復習リストを処理してくれる。",
    ),
    "one of the": CardCopy(
        "部分表現",
        "複数の中の一つ: one of the + 最上級/複数名詞",
        "後ろに集合が来る。oneを単独で訳さず、全体から一つを取り出す形で読む。",
        "This is one of the phrases worth learning first.",
        "これは最初に覚える価値があるフレーズの一つだ。",
    ),
    "the united states": CardCopy(
        "固有名詞",
        "the United States: アメリカ合衆国",
        "theを含めて国名として一まとまりで読む。",
        "The United States has many regional accents.",
        "アメリカ合衆国には多くの地域アクセントがある。",
    ),
    "out of the": CardCopy(
        "範囲表現",
        "...の中から / ...の外へ: out of the",
        "後ろに範囲や場所が続き、そこから外へ出る・選ぶ・生じる感覚で読む。",
        "Choose the best example out of the list.",
        "一覧の中から最もよい例を選ぶ。",
    ),
    "part of the": CardCopy(
        "部分表現",
        "...の一部: part of the + 全体",
        "全体の中に含まれる一部として読む。",
        "This pattern is part of the core deck.",
        "この型はコアデッキの一部だ。",
    ),
    "the end of": CardCopy(
        "位置・時間表現",
        "...の終わり: the end of + 範囲",
        "終点となる範囲をofの後ろで受ける。",
        "The note appears at the end of the card.",
        "メモはカードの終わりに表示される。",
    ),
    "do not know": CardCopy(
        "否定表現",
        "分からない / 知らない: do not know",
        "knowを否定する基本形。会話ではdon't knowにもなる。",
        "You do not know a word fully until you know its partners.",
        "一緒に使われる語を知らなければ、その単語を十分に知っているとは言えない。",
    ),
    "the fact that": CardCopy(
        "名詞節表現",
        "...という事実: the fact that + 文",
        "that以下の文を、factの内容として名詞化して読む。",
        "The fact that it appears often makes it worth reviewing.",
        "それが頻繁に出るという事実が、復習する価値を生む。",
    ),
    "the use of": CardCopy(
        "名詞化表現",
        "...の使用: the use of + 名詞",
        "useを名詞として受け、何を使うのかをofの後ろで示す。",
        "The use of examples makes the card clearer.",
        "例文の使用によってカードは分かりやすくなる。",
    ),
    "be able to": CardCopy(
        "可能表現",
        "...できる: be able to + 動詞",
        "able toより文中での形が見えやすい。主語ができる状態にあると読む。",
        "You will be able to read faster with repeated practice.",
        "繰り返し練習すれば、より速く読めるようになる。",
    ),
    "the number of": CardCopy(
        "数量表現",
        "...の数: the number of + 複数名詞",
        "a number ofとは違い、数そのものを主語・目的語として扱う。",
        "The number of review cards changes every day.",
        "復習カードの数は毎日変わる。",
    ),
    "a number of": CardCopy(
        "数量表現",
        "いくつもの: a number of + 複数名詞",
        "the number ofと違い、複数のものがあることを表す。",
        "A number of phrases share the same pattern.",
        "いくつものフレーズが同じ型を共有している。",
    ),
    "cannot be": CardCopy(
        "否定可能表現",
        "...であるはずがない / ...され得ない: cannot be",
        "beの後ろに形容詞・名詞・過去分詞が来て、不可能性を示す。",
        "A phrase cannot be understood from one word alone.",
        "フレーズは単語一つだけからは理解できない。",
    ),
    "not want to": CardCopy(
        "否定希望表現",
        "...したくない: not want to + 動詞",
        "want toの否定形として、望まない行動を後ろに置く。",
        "You may not want to review every card at once.",
        "すべてのカードを一度に復習したいとは思わないかもしれない。",
    ),
    "the rest of": CardCopy(
        "残余表現",
        "残りの...: the rest of + 名詞",
        "全体からすでに扱った部分を除いた残りを示す。",
        "The rest of the deck can wait until tomorrow.",
        "デッキの残りは明日まで待ってもよい。",
    ),
    "the same time": CardCopy(
        "時間表現",
        "同じ時 / 同時: the same time",
        "at the same timeの一部としても、同じ時間を指す名詞句としても出る。",
        "They opened the app at the same time.",
        "彼らは同時にアプリを開いた。",
    ),
    "side of the": CardCopy(
        "位置表現",
        "...の側: side of the + 名詞",
        "左右・内外・立場など、どちら側かを後ろで限定する。",
        "The icon is on the right side of the card.",
        "アイコンはカードの右側にある。",
    ),
    "back to the": CardCopy(
        "復帰表現",
        "...へ戻る: back to the + 場所/状態",
        "前にいた場所や状態へ戻る流れとして読む。",
        "Swipe back to the previous card if you make a mistake.",
        "間違えたら前のカードへ戻す。",
    ),
    "at the time": CardCopy(
        "時間表現",
        "その時点で: at the time",
        "過去や特定の状況の一点を指す。",
        "At the time, the phrase looked unfamiliar.",
        "その時点では、そのフレーズは見慣れないものに見えた。",
    ),
    "according to the": CardCopy(
        "出典表現",
        "...によると: according to the + 資料/人物",
        "後ろに来る情報源を根拠として受ける。",
        "According to the data, this phrase is common.",
        "データによると、このフレーズは一般的だ。",
    ),
    "based on the": CardCopy(
        "根拠表現",
        "...に基づいて: based on the + 名詞",
        "判断や設計の土台を後ろに置く。",
        "The order is based on the frequency list.",
        "順序は頻度リストに基づいている。",
    ),
    "in which the": CardCopy(
        "関係詞表現",
        "その中で...: in which the + 文",
        "前の名詞を受け、その内部で何が起きるかを説明する。",
        "The app shows a card in which the phrase stays visible.",
        "そのアプリはフレーズが見えたままのカードを表示する。",
    ),
    "the case of": CardCopy(
        "場合表現",
        "...の場合: the case of + 名詞",
        "特定の例や状況を取り上げる時に使う。",
        "In the case of short phrases, context matters.",
        "短いフレーズの場合、文脈が重要だ。",
    ),
    "the development of": CardCopy(
        "名詞化表現",
        "...の発展 / 開発: the development of + 名詞",
        "developする過程や成果を名詞として受ける。",
        "The development of the app started with a small deck.",
        "そのアプリの開発は小さなデッキから始まった。",
    ),
    "in the world": CardCopy(
        "範囲表現",
        "世界で / 世の中で: in the world",
        "最上級や一般論の範囲としてよく使われる。",
        "English is used in many places in the world.",
        "英語は世界の多くの場所で使われている。",
    ),
    "of the world": CardCopy(
        "所属表現",
        "世界の: of the world",
        "前の名詞が世界全体やその一部に属することを示す。",
        "The languages of the world share surprising patterns.",
        "世界の言語は驚くほど共通した型を持っている。",
    ),
    "the first time": CardCopy(
        "経験表現",
        "初めて / 最初の時: the first time",
        "経験の初回や出来事の最初を示す。",
        "The first time you see a phrase, just tap to check it.",
        "初めてフレーズを見たら、タップして確認すればよい。",
    ),
    "in the case": CardCopy(
        "場合表現",
        "その場合には: in the case",
        "ofが続くと、どの場合なのかが具体化される。",
        "In the case of common words, collocations reduce ambiguity.",
        "一般的な単語の場合、コロケーションが曖昧さを減らす。",
    ),
    "the presence of": CardCopy(
        "存在表現",
        "...の存在: the presence of + 名詞",
        "あるものが存在することを名詞句として扱う。",
        "The presence of context makes the meaning clearer.",
        "文脈があることで意味はより明確になる。",
    ),
    "was going to": CardCopy(
        "予定表現",
        "...するつもりだった: was going to + 動詞",
        "過去の時点で予定・意図・成り行きがあったことを示す。",
        "She was going to skip the card, but the example helped.",
        "彼女はそのカードを飛ばすつもりだったが、例文が助けになった。",
    ),
    "due to the": CardCopy(
        "原因表現",
        "...が原因で: due to the + 名詞",
        "後ろの名詞を原因として受ける、やや硬い表現。",
        "The delay was due to the large data file.",
        "遅れは大きなデータファイルが原因だった。",
    ),
    "a couple of": CardCopy(
        "数量表現",
        "二、三の: a couple of + 複数名詞",
        "厳密な二つではなく、少数をゆるく表すことも多い。",
        "Review a couple of cards before bed.",
        "寝る前に数枚のカードを復習する。",
    ),
    "the role of": CardCopy(
        "役割表現",
        "...の役割: the role of + 名詞",
        "何がどんな働きを持つかを説明する。",
        "The role of examples is to make usage concrete.",
        "例文の役割は使い方を具体的にすることだ。",
    ),
    "going to be": CardCopy(
        "未来状態表現",
        "...になる / ...である予定: going to be",
        "これから起きる状態や評価を予測・予定として読む。",
        "The next version is going to be easier to maintain.",
        "次の版はより保守しやすくなる予定だ。",
    ),
    "rest of the": CardCopy(
        "残余表現",
        "残りの: rest of the + 名詞",
        "全体のうち未処理の部分をまとめて指す。",
        "Save the rest of the cards for tomorrow.",
        "残りのカードは明日に取っておく。",
    ),
    "the back of": CardCopy(
        "位置表現",
        "...の後ろ / 裏側: the back of + 名詞",
        "物理的な後ろ側や、カードの裏面を指す時に使う。",
        "The explanation appears on the back of the card.",
        "説明はカードの裏面に表示される。",
    ),
    "with respect to": CardCopy(
        "観点表現",
        "...に関して: with respect to + 名詞",
        "話題や評価の対象を限定する、硬めの表現。",
        "With respect to reading, frequency is only one factor.",
        "読解に関しては、頻度は一つの要素にすぎない。",
    ),
    "need to be": CardCopy(
        "必要表現",
        "...である必要がある / ...される必要がある: need to be",
        "後ろに形容詞・名詞・過去分詞を置いて、必要な状態を示す。",
        "The cards need to be short enough for one-handed use.",
        "カードは片手操作に十分短い必要がある。",
    ),
    "for a moment": CardCopy(
        "時間表現",
        "少しの間: for a moment",
        "短い時間だけ続く動作や状態を示す。",
        "Pause for a moment before you swipe.",
        "スワイプする前に少しだけ止まる。",
    ),
}
PREPOSITION_JA = {
    "about": "話題・周辺",
    "after": "後続・時間",
    "against": "対立・接触",
    "among": "集団の中",
    "around": "周辺・およそ",
    "as": "役割・同等",
    "at": "一点・場面",
    "before": "前",
    "between": "二者間",
    "by": "手段・近接",
    "during": "期間内",
    "for": "目的・対象",
    "from": "起点",
    "in": "内部・状況",
    "into": "内部への移動",
    "of": "所属・部分",
    "on": "接触・話題",
    "over": "上方・超過",
    "through": "通過・手段",
    "to": "方向・到達点",
    "with": "同伴・手段",
    "within": "範囲内",
    "without": "欠如",
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


def normalized_key(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def content_words(text: str) -> list[str]:
    return [word for word in tokens(text) if word not in FUNCTION_WORDS]


def quality_rejection_reason(candidate: Candidate) -> str | None:
    text = candidate.text
    lowered = normalized_key(text)
    words = tokens(text)

    if any(pattern in lowered for pattern in REJECT_PATTERNS):
        return "source_noise"
    if re.search(r"\b[a-z]+@[a-z]+", lowered):
        return "email_or_url_noise"
    if len(words) < 2:
        return "too_short"
    if any(len(word) == 1 and word not in {"a", "i"} for word in words):
        return "token_fragment"
    if lowered in UTILITY_COPIES:
        return None
    if "," in text:
        return "punctuation_fragment"
    if lowered in LOW_VALUE_EXACT:
        return "low_value_exact"
    if all(word in FUNCTION_WORDS for word in words):
        return "function_words_only"
    if words[-1] in DETERMINERS | COORDINATORS:
        return "trailing_function_word"
    if candidate.gram >= 3 and words[-1] in ADJECTIVE_ENDINGS | {"united"}:
        return "trailing_modifier"
    if words[0] in PRONOUNS | AUXILIARY_CONTRACTIONS and len(content_words(text)) < 2:
        return "pronoun_stub"
    if len(words) == 2 and all(word in PRONOUNS | BE_FORMS | HAVE_FORMS | DO_FORMS | MODALS | NEGATIVES for word in words):
        return "auxiliary_fragment"
    if len(words) == 2 and words[0] in COORDINATORS and words[1] in DETERMINERS | PRONOUNS:
        return "coordinator_stub"
    if candidate.gram == 2 and len(content_words(text)) == 1 and words[0] in PREPOSITIONS and words[1] in DETERMINERS:
        return "bare_preposition_stub"
    return None


def target_words(text: str) -> list[dict[str, str]]:
    words = content_words(text)
    if not words:
        words = tokens(text)
    unique: list[str] = []
    for word in words:
        if word not in unique:
            unique.append(word)
    return [{"lemma": word} for word in unique[:4]]


def tags_for(text: str, gram: int) -> list[str]:
    words = tokens(text)
    tags = [f"{gram}-gram"]
    if any(word in words for word in ("not", "cannot", "no", "never")):
        tags.append("negative")
    if any(word in words for word in ("if", "when", "because", "while")):
        tags.append("connector")
    if any(word in words for word in ("can", "could", "may", "might", "would", "should", "will")):
        tags.append("modal")
    if any(word in words for word in ("of", "in", "on", "at", "from", "with", "to")):
        tags.append("structure")
    return tags[:4]


def reading_copy_for(text: str) -> CardCopy:
    lowered = normalized_key(text)
    if lowered in UTILITY_COPIES:
        return UTILITY_COPIES[lowered]

    words = tokens(text)
    focus = content_words(text)
    focus_text = " / ".join(focus[:3]) if focus else " / ".join(words[:3])

    if words[0] in CONNECTORS:
        connector = words[0]
        return CardCopy(
            "接続チャンク",
            f"{text}: 文と文の関係を作るまとまり",
            f"{connector}から始まる部分を条件・理由・時間などの節として先に受け、主文につなげて読む。中心語: {focus_text}。",
        )

    if len(words) >= 3 and words[0] in PREPOSITIONS and words[1] in DETERMINERS:
        prep = words[0]
        label = PREPOSITION_JA.get(prep, "前置詞の関係")
        return CardCopy(
            "前置詞句",
            f"{text}: {label}を作る前置詞句",
            f"{prep}を単独で訳さず、後ろの名詞まとまりまで一気に受ける。中心語: {focus_text}。",
        )

    if words[0] in PREPOSITIONS:
        prep = words[0]
        label = PREPOSITION_JA.get(prep, "前置詞の関係")
        return CardCopy(
            "前置詞コロケーション",
            f"{text}: {label}で後ろへつなぐまとまり",
            f"文中では副詞句や形容詞句として働きやすい。前置詞の後ろに何を受けるかを意識する。中心語: {focus_text}。",
        )

    if "of" in words:
        return CardCopy(
            "ofコロケーション",
            f"{text}: 所属・部分・内容を後ろで限定するまとまり",
            f"ofの前後をばらばらに訳さず、前の名詞を後ろの名詞で説明する関係として読む。中心語: {focus_text}。",
        )

    if words[0] == "to":
        return CardCopy(
            "to不定詞チャンク",
            f"{text}: 目的・方向・これからの動きを表すまとまり",
            f"toの後ろを動作のまとまりとして受け、前の語が要求する方向を読む。中心語: {focus_text}。",
        )

    if words[-1] == "to":
        return CardCopy(
            "動詞+toコロケーション",
            f"{text}: 後ろに動作や到達点を要求するまとまり",
            f"最後のtoで止めず、この後に来る動詞や名詞へ意味が伸びる合図として読む。中心語: {focus_text}。",
        )

    if any(word in MODALS for word in words):
        return CardCopy(
            "助動詞チャンク",
            f"{text}: 可能性・意志・義務などを加えるまとまり",
            f"助動詞を単独で訳さず、後ろの動詞まで含めて話し手の判断として読む。中心語: {focus_text}。",
        )

    if any(word in BE_FORMS | HAVE_FORMS | DO_FORMS for word in words):
        return CardCopy(
            "文法コロケーション",
            f"{text}: 時制・状態・否定・強調を作るまとまり",
            f"be/have/doは周辺語と組んで機能が決まる。語順ごと覚えると読解で迷いにくい。中心語: {focus_text}。",
        )

    if words[0] in DETERMINERS:
        return CardCopy(
            "名詞句コロケーション",
            f"{text}: 名詞を限定するまとまり",
            f"冠詞・限定詞から中心名詞までを一つの名詞句として受ける。中心語: {focus_text}。",
        )

    if any(word in {"more", "most", "less", "least", "than"} for word in words):
        return CardCopy(
            "比較チャンク",
            f"{text}: 比較や程度を表すまとまり",
            f"基準や範囲が後ろに続きやすいので、比較の方向を先に押さえて読む。中心語: {focus_text}。",
        )

    return CardCopy(
        "語彙コロケーション",
        f"{text}: 高頻度で一緒に現れる語のまとまり",
        f"単語を一つずつ訳す前に、この並びを見慣れた表現として処理する。中心語: {focus_text}。",
    )


def make_card(candidate: Candidate, overall_rank: int, quality_tier: str = "core") -> dict[str, object]:
    focus = target_words(candidate.text)
    copy = reading_copy_for(candidate.text)
    card = {
        "id": f"ng-{overall_rank:05d}-{slugify(candidate.text)}",
        "kind": "ngram",
        "text": candidate.text,
        "corpusText": candidate.corpus_text,
        "readingType": copy.reading_type,
        "meaning": copy.meaning,
        "note": copy.note,
        "gram": candidate.gram,
        "rank": overall_rank,
        "sourceRank": candidate.source_rank,
        "freq": candidate.freq,
        "source": SOURCE_LABELS[candidate.source_key],
        "sourceList": candidate.source_key,
        "qualityTier": quality_tier,
        "tags": tags_for(candidate.text, candidate.gram),
        "targetWords": focus,
    }
    if copy.example and copy.example_ja:
        card["example"] = copy.example
        card["exampleJa"] = copy.example_ja
        card["exampleStatus"] = "manual"
    return card


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


def source_priority(candidate: Candidate) -> tuple[int, int, int]:
    source_order = 0 if candidate.source_key == "english" else 1
    return (source_order, candidate.source_rank, -candidate.freq)


def support_acceptance_reason(candidate: Candidate, strict_reason: str | None) -> str | None:
    if strict_reason is None:
        return "core"

    words = tokens(candidate.text)
    if not words or "," in candidate.text:
        return None
    if strict_reason == "pronoun_stub" and candidate.gram >= 3 and len(content_words(candidate.text)) >= 1:
        return "pronoun_pattern"
    if words[0] in PRONOUNS | AUXILIARY_CONTRACTIONS | COORDINATORS:
        return None

    if strict_reason == "function_words_only" and candidate.gram >= 3:
        return "grammar_pattern"
    if strict_reason == "trailing_modifier" and candidate.gram >= 3 and len(content_words(candidate.text)) >= 1:
        return "modifier_pattern"
    if strict_reason == "trailing_function_word" and candidate.gram >= 3 and len(content_words(candidate.text)) >= 1:
        return "collocation_stem"
    return None


def final_priority(candidate: Candidate, quality_tier: str = "core") -> tuple[int, int, int, int, int, int]:
    manual_order = 0 if normalized_key(candidate.text) in UTILITY_COPIES else 1
    tier_order = 0 if quality_tier == "core" else 1
    source_order = 0 if candidate.source_key == "english" else 1
    gram_order = {3: 0, 4: 1, 2: 2, 5: 3}[candidate.gram]
    return (manual_order, tier_order, source_order, gram_order, candidate.source_rank, -candidate.freq)


def build_deck() -> dict[str, object]:
    candidates, raw_counts = load_candidates()
    selected: list[Candidate] = []
    seen: set[str] = set()
    rejected_by_reason: Counter[str] = Counter()
    recovered_by_reason: Counter[str] = Counter()
    quality_tiers: dict[str, str] = {}

    for gram, target in GRAM_TARGETS.items():
        gram_selected = 0
        for candidate in sorted((item for item in candidates if item.gram == gram), key=source_priority):
            key = normalized_key(candidate.text)
            if key in seen:
                continue
            reason = quality_rejection_reason(candidate)
            if reason:
                rejected_by_reason[reason] += 1
                continue
            seen.add(key)
            selected.append(candidate)
            quality_tiers[key] = "core"
            gram_selected += 1
            if gram_selected == target:
                break

    if len(selected) < TARGET_COUNT:
        for candidate in sorted(candidates, key=final_priority):
            key = normalized_key(candidate.text)
            if key in seen:
                continue
            reason = quality_rejection_reason(candidate)
            if reason:
                rejected_by_reason[reason] += 1
                continue
            seen.add(key)
            selected.append(candidate)
            quality_tiers[key] = "core"
            if len(selected) == TARGET_COUNT:
                break

    if len(selected) < TARGET_COUNT:
        for candidate in sorted(candidates, key=final_priority):
            key = normalized_key(candidate.text)
            if key in seen:
                continue
            reason = quality_rejection_reason(candidate)
            support_reason = support_acceptance_reason(candidate, reason)
            if not support_reason:
                continue
            seen.add(key)
            selected.append(candidate)
            quality_tiers[key] = "support"
            recovered_by_reason[support_reason] += 1
            if len(selected) == TARGET_COUNT:
                break

    if len(selected) != TARGET_COUNT:
        raise RuntimeError(f"Expected {TARGET_COUNT} cards, got {len(selected)}")

    selected = sorted(selected, key=lambda candidate: final_priority(candidate, quality_tiers[normalized_key(candidate.text)]))
    cards = [
        make_card(candidate, index, quality_tiers[normalized_key(candidate.text)])
        for index, candidate in enumerate(selected, start=1)
    ]
    selected_by_source = Counter(card["sourceList"] for card in cards)
    selected_by_gram = Counter(str(card["gram"]) for card in cards)
    selected_by_quality_tier = Counter(card["qualityTier"] for card in cards)
    manual_examples = sum(1 for card in cards if card.get("exampleStatus") == "manual")
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
            "selectedByQualityTier": dict(sorted(selected_by_quality_tier.items())),
            "manualExamples": manual_examples,
            "rejectedByQualityFilter": sum(rejected_by_reason.values()),
            "rejectedByReason": dict(sorted(rejected_by_reason.items())),
            "recoveredAsSupport": dict(sorted(recovered_by_reason.items())),
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
