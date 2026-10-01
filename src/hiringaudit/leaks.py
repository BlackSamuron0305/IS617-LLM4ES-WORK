"""Origin-cue ("leak") scanning for CVs, job ads and prompt texts (review M6).

Rules come from config/leak_terms.csv (one row per term) plus every demonym and
country name in stimuli/nationalities.csv (case-sensitive, whole word).

Columns of leak_terms.csv: ``term``; ``category`` (a label: cities, german,
regions, languages, country_forms, citizenship, religion, ...); ``scope`` = ``all``
(every rendered CV outside its Nationality line, every job ad, the system prompt,
every assembled prompt template without the neutrality paragraph, the
principle-probe contexts) or ``texts`` (all of those except the CVs);
``match_type`` = ``word`` (literal, whole word, exact case), ``word_ignore_case``
(literal, whole word, any case), ``regex_ignore_case`` (a regular expression,
whole word, any case) or ``character`` (forbidden anywhere, e.g. umlauts);
``allowed_on_cv_line`` = the label of a CV line on which the term is allowed
(e.g. ``Work authorization``: "visa" in "...; no visa sponsorship required");
``note``.

Base countries (user request 2026-10-01): a CV or job ad set in a base country
may name that country and its cities. Those phrases are masked before scanning
(``allowed_phrases``), so "United Arab Emirates" does not trip the "Arab" rule
and "Saudi Arabia" does not trip the "Saudi" demonym, while every other
country, city and demonym stays forbidden.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import csvio
from .config import NationalitySet
from .stimuli.setting import BaseCountry

NATIONALITY_PREFIX = "Nationality: "
LEAK_TERM_COLUMNS = ("term", "category", "scope", "match_type", "allowed_on_cv_line", "note")
SCOPES = ("all", "texts")
MATCH_TYPES = ("word", "word_ignore_case", "regex_ignore_case", "character")


def _alternation(tokens, flags=0, regex: set[str] | None = None) -> re.Pattern | None:
    """Whole-word alternation of ``tokens``; tokens in ``regex`` are used as regular
    expressions, every other token literally."""
    toks = sorted({t for t in tokens if t}, key=len, reverse=True)
    if not toks:
        return None
    parts = [t if t in (regex or set()) else re.escape(t) for t in toks]
    return re.compile(r"(?<![\w])(" + "|".join(parts) + r")(?![\w])", flags)


def mask_phrases(line: str, phrases: set[str] | None) -> str:
    """Replace whole-word occurrences of ``phrases`` (longest first) by '#' runs of
    the same length, so the masked text can never match a leak term."""
    pat = _alternation(phrases or ())
    if pat is None:
        return line
    return pat.sub(lambda m: "#" * len(m.group(0)), line)


@dataclass
class LeakRules:
    base_countries: dict[str, BaseCountry]
    cv_allowed: set[tuple[str, str]]
    case_sensitive: re.Pattern | None
    case_insensitive: re.Pattern | None
    texts_only: re.Pattern | None = None
    texts_only_case_sensitive: re.Pattern | None = None
    forbidden_characters: tuple[str, ...] = ()
    term_count: int = 0
    categories: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path, nationalities: NationalitySet,
             base_countries: dict[str, BaseCountry]) -> "LeakRules":
        """``path`` = config/leak_terms.csv; ``base_countries`` from stimuli/base_countries.csv
        (``stimuli.setting.load_base_countries``)."""
        cs, ci, texts_cs, texts_ci, chars, regex, cats = [], [], [], [], [], set(), {}
        allowed = set()
        for r in csvio.read_rows(path, LEAK_TERM_COLUMNS, allowed=LEAK_TERM_COLUMNS):
            term, cat = csvio.text(r["term"]), csvio.text(r["category"])
            scope, mt = csvio.text(r["scope"]), csvio.text(r["match_type"])
            at = csvio.where(path, term)
            if not term:
                raise csvio.TableError(f"{at}: empty term")
            if scope not in SCOPES:
                raise csvio.TableError(f"{at}: scope must be one of {SCOPES}, got {scope!r}")
            if mt not in MATCH_TYPES:
                raise csvio.TableError(f"{at}: match_type must be one of {MATCH_TYPES}, got {mt!r}")
            if mt == "character":
                if scope != "all" or len(term) != 1:
                    raise csvio.TableError(f"{at}: a 'character' term is one character with scope 'all'")
                chars.append(term)
                continue
            if mt == "regex_ignore_case":
                regex.add(term)
            target = {("all", False): cs, ("all", True): ci, ("texts", False): texts_cs,
                      ("texts", True): texts_ci}[(scope, mt != "word")]
            target.append(term)
            cats.setdefault(cat, []).append(term)
            line = csvio.text(r["allowed_on_cv_line"])
            if line:
                allowed.add((f"{line}: ", term))
        for n in nationalities.conditions:
            cs += [n.demonym, n.country]
        return cls(
            base_countries=dict(base_countries),
            cv_allowed=allowed,
            case_sensitive=_alternation(cs, regex=regex),
            case_insensitive=_alternation(ci, re.IGNORECASE, regex=regex),
            texts_only=_alternation(texts_ci, re.IGNORECASE, regex=regex),
            texts_only_case_sensitive=_alternation(texts_cs, regex=regex),
            forbidden_characters=tuple(chars),
            term_count=len(set(cs) | set(ci)),
            categories=cats,
        )

    def allowed_phrases(self, base_country: str | None) -> set[str]:
        b = self.base_countries.get(base_country or "")
        return b.allowed_phrases() if b else set()

    def _hits(self, line: str, texts: bool = False, allowed_phrases: set[str] | None = None) -> list[str]:
        line = mask_phrases(line, allowed_phrases)
        out = []
        pats = (self.case_sensitive, self.case_insensitive) + (
            (self.texts_only, self.texts_only_case_sensitive) if texts else ())
        for pat in pats:
            if pat is not None:
                out += [m.group(1) for m in pat.finditer(line)]
        out += [ch for ch in self.forbidden_characters if ch in line]
        return out

    def scan_cv(self, text: str, allowed_phrases: set[str] | None = None) -> list[str]:
        """Cues anywhere in a CV except its Nationality line, allowed line/token pairs
        and the place names of the CV's base country (``allowed_phrases``)."""
        leaks = []
        for i, line in enumerate(text.split("\n"), start=1):
            if line.startswith(NATIONALITY_PREFIX):
                continue
            for tok in self._hits(line, allowed_phrases=allowed_phrases):
                if any(line.startswith(p) and tok == t for p, t in self.cv_allowed):
                    continue
                leaks.append(f"line {i}: {tok!r} in {line[:80]!r}")
        return leaks

    def scan_text(self, text: str, allowed_phrases: set[str] | None = None) -> list[str]:
        """Cues in free text (job ads, prompts); ``allowed_phrases`` (the base-country
        place names of a localized job ad) are exempt."""
        leaks = []
        for i, line in enumerate(text.split("\n"), start=1):
            for tok in self._hits(line, texts=True, allowed_phrases=allowed_phrases):
                leaks.append(f"line {i}: {tok!r} in {line[:80]!r}")
        return leaks
