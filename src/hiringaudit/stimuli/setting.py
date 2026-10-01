"""The setting of a CV: its base country (user request 2026-10-01).

Every CV is set entirely in ONE Arab League country, its *base country*: the
current location, every employer city and every educational institution are in
that country, and the job ad the CV is shown with is located in the CV's base
city. The base countries and their cities are defined in
``stimuli/base_countries.csv`` (one row per country) and their institutions in
``stimuli/building_blocks/institutions.csv`` (one row per institution and
programme kind); both are the builder's input and the validator's whitelist.

The three personal-details lines that depend on the base country are derived
here, so that the table builder and the validator agree on their exact wording:

    Location: <base city>, <country>
    Work authorization: Authorized to work in <the country>; no visa sponsorship required
    Driving licence: Valid driving licence issued in <the country>

``host_national`` (nationality code == base country) is derived from the CV's
``base_country`` when records are written and parsed; benchmark, placebo and
NONE codes are never host nationals because every base country is an Arab
League member state.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .. import csvio

LOCATION_FORMAT = "{city}, {country}"
WORK_AUTHORIZATION_FORMAT = "Authorized to work in {the_country}; no visa sponsorship required"
DRIVING_LICENCE_FORMAT = "Valid driving licence issued in {the_country}"
INSTITUTION_KINDS = ("computing", "business", "engineering", "college")


@dataclass(frozen=True)
class BaseCountry:
    code: str                                  # ISO3, a row of stimuli/nationalities.csv
    name: str                                  # country name as in stimuli/nationalities.csv
    article: str                               # "the " for "the United Arab Emirates", else ""
    aliases: tuple[str, ...]                   # other forms that may appear (e.g. "UAE" in "UAE University")
    base_city: str                             # the city of the Location line and of the job ad
    cities: tuple[str, ...]                    # every city an employer may be in (includes base_city)
    institutions: dict[str, tuple[str, ...]]   # programme kind (INSTITUTION_KINDS) -> real institutions

    @property
    def the_name(self) -> str:
        return f"{self.article}{self.name}"

    @property
    def all_institutions(self) -> set[str]:
        return {i for v in self.institutions.values() for i in v}

    def personal_lines(self) -> dict[str, str]:
        """The exact values of the base-country personal-details lines."""
        return {
            "location": LOCATION_FORMAT.format(city=self.base_city, country=self.name),
            "work_authorization": WORK_AUTHORIZATION_FORMAT.format(the_country=self.the_name),
            "driving_licence": DRIVING_LICENCE_FORMAT.format(the_country=self.the_name),
        }

    def allowed_phrases(self) -> set[str]:
        """Place names a CV or job ad set in this country may contain (the leak check
        masks them before scanning; every other country or city name stays forbidden)."""
        return {self.name, *self.aliases, *self.cities}


BASE_COUNTRY_COLUMNS = ("code", "name", "article", "aliases", "base_city", "cities")
INSTITUTION_COLUMNS = ("base_country", "institution_kind", "institution")


def load_base_countries(path: str | Path, institutions_path: str | Path) -> dict[str, BaseCountry]:
    """Read ``stimuli/base_countries.csv`` and ``stimuli/building_blocks/institutions.csv``.

    ``article`` is ``the`` for names used with the definite article ("the United
    Arab Emirates"), else empty; ``aliases`` and ``cities`` are " | "-lists.
    Institutions keep their row order within (country, kind): the builder draws
    from them in that order.
    """
    inst: dict[str, dict[str, list[str]]] = {}
    for r in csvio.read_rows(institutions_path, INSTITUTION_COLUMNS, allowed=INSTITUTION_COLUMNS):
        code, kind, name = (csvio.text(r[c]) for c in INSTITUTION_COLUMNS)
        if kind not in INSTITUTION_KINDS:
            raise ValueError(f"{csvio.where(institutions_path, name)}: unknown institution kind {kind!r} "
                             f"(kinds: {INSTITUTION_KINDS})")
        inst.setdefault(code, {}).setdefault(kind, []).append(name)
    out: dict[str, BaseCountry] = {}
    for r in csvio.read_rows(path, BASE_COUNTRY_COLUMNS, allowed=BASE_COUNTRY_COLUMNS):
        code = csvio.text(r["code"])
        at = csvio.where(path, code)
        cities = tuple(csvio.items(r["cities"]))
        base_city = csvio.text(r["base_city"])
        if base_city not in cities:
            raise ValueError(f"{at}: base_city {base_city!r} must be one of its cities")
        article = csvio.text(r["article"])
        if article not in ("", "the"):
            raise ValueError(f"{at}: article must be empty or 'the', got {article!r}")
        out[code] = BaseCountry(code=code, name=csvio.text(r["name"]), article=f"{article} " if article else "",
                                aliases=tuple(csvio.items(r["aliases"])), base_city=base_city, cities=cities,
                                institutions={k: tuple(v) for k, v in inst.get(code, {}).items()})
    unknown = sorted(set(inst) - set(out))
    if unknown:
        raise ValueError(f"{institutions_path}: institutions for unknown base countries {unknown}")
    return out
