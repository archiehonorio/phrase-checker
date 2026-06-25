"""Local (offline) engine — pure Python, no Java, no network, fully private.

Goes beyond spelling: it also fixes the most common everyday grammar/phrasing
mistakes in workplace writing — missing contractions, "could of" -> "could
have", a/an, repeated words, spacing, punctuation and capitalization.

It is rule-based, so it can't creatively rewrite tone the way the AI engine can,
but it is a genuine quick-fix, not just a spell checker.
"""

from __future__ import annotations

import re
from functools import lru_cache

try:
    from spellchecker import SpellChecker  # type: ignore
    _HAS_SPELL = True
except Exception:  # pragma: no cover - optional dependency
    _HAS_SPELL = False


@lru_cache(maxsize=1)
def _speller():
    return SpellChecker(distance=1)


_WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")

# Multi-word phrase fixes (applied first, case-insensitive).
_PHRASE_FIXES = [
    (r"\bcould of\b", "could have"),
    (r"\bwould of\b", "would have"),
    (r"\bshould of\b", "should have"),
    (r"\bmust of\b", "must have"),
    (r"\bmight of\b", "might have"),
    (r"\bkind of\b", "kind of"),
    (r"\ba lot of\b", "a lot of"),
]

# Single-word fixes: misspelt contractions, slang -> proper form.
# Keys are lowercase; capitalization of the result is handled separately.
_WORD_FIXES = {
    "dont": "don't", "cant": "can't", "wont": "won't", "isnt": "isn't",
    "arent": "aren't", "wasnt": "wasn't", "werent": "weren't",
    "doesnt": "doesn't", "didnt": "didn't", "hasnt": "hasn't",
    "havent": "haven't", "hadnt": "hadn't", "wouldnt": "wouldn't",
    "couldnt": "couldn't", "shouldnt": "shouldn't", "mustnt": "mustn't",
    "im": "I'm", "ive": "I've", "youre": "you're", "theyre": "they're",
    "thats": "that's", "whats": "what's", "heres": "here's",
    "theres": "there's", "whos": "who's", "lets": "let's",
    "gonna": "going to", "wanna": "want to", "gotta": "got to",
    "kinda": "kind of", "alot": "a lot", "teh": "the", "u": "you",
    "ur": "your", "pls": "please", "plz": "please", "thx": "thanks",
    "tho": "though", "ofcourse": "of course",
}


def _apply_phrases(text: str) -> str:
    for pat, repl in _PHRASE_FIXES:
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    return text


def _match_case(original: str, replacement: str) -> str:
    if original[:1].isupper() and not replacement.startswith("I"):
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _apply_word_fixes(text: str) -> str:
    def repl(m: re.Match) -> str:
        word = m.group(0)
        fix = _WORD_FIXES.get(word.lower())
        return _match_case(word, fix) if fix else word

    return re.sub(r"[A-Za-z]+", repl, text)


def _fix_spelling(text: str) -> str:
    if not _HAS_SPELL:
        return text
    sp = _speller()

    def repl(m: re.Match) -> str:
        word = m.group(0)
        if word.isupper() or not any(c.islower() for c in word) or "'" in word:
            return word
        if word.lower() in sp:
            return word
        suggestion = sp.correction(word.lower())
        if not suggestion or suggestion == word.lower():
            return word
        if word[0].isupper():
            suggestion = suggestion.capitalize()
        return suggestion

    return _WORD_RE.sub(repl, text)


def _fix_articles(text: str) -> str:
    # "a apple" -> "an apple"
    text = re.sub(
        r"\b([Aa])\s+([aeiouAEIOU]\w*)", lambda m: ("An" if m.group(1) == "A" else "an") + " " + m.group(2), text
    )
    # "an book" -> "a book"  (skip silent-h words; good enough for common cases)
    text = re.sub(
        r"\b([Aa])n\s+([b-df-hj-np-tv-zB-DF-HJ-NP-TV-Z]\w*)",
        lambda m: ("A" if m.group(1) == "A" else "a") + " " + m.group(2),
        text,
    )
    return text


def _collapse_repeats(text: str) -> str:
    # "the the" -> "the"  (only obvious accidental doubles)
    return re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)


def _fix_whitespace(text: str) -> str:
    text = text.replace("\t", " ")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,;:])(?=[^\s\d])", r"\1 ", text)
    text = re.sub(r"([.!?])(?=[A-Za-z])", r"\1 ", text)
    text = re.sub(r"[ ]+\n", "\n", text)
    return text.strip()


def _fix_capitalization(text: str) -> str:
    text = re.sub(r"(^\s*[a-z])", lambda m: m.group(0).upper(), text)
    text = re.sub(
        r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text
    )
    text = re.sub(r"\bi\b", "I", text)
    text = re.sub(r"\bi'", "I'", text)
    return text


def check_local(text: str) -> dict:
    """Return the offline-corrected text."""
    fixed = _apply_phrases(text)
    fixed = _apply_word_fixes(fixed)
    fixed = _fix_spelling(fixed)
    fixed = _fix_articles(fixed)
    fixed = _collapse_repeats(fixed)
    fixed = _fix_whitespace(fixed)
    fixed = _fix_capitalization(fixed)
    return {"result": fixed, "engine": "local", "note": ""}
