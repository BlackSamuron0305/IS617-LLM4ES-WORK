"""Prompts: assembled from structured parts (prompts/prompt_parts.csv) by recipes
(prompts/prompt_recipes.csv). See prompts/README.md for a worked example.

prompt_parts.csv     one row per piece of fixed text: part_id, role (system | user),
                     part_type, task, variant, text (``{placeholders}`` allowed only
                     where documented: ``{title}`` in the occupation probe context)
prompt_recipes.csv   one row per step: condition, task, variant, step (1..n), and
                     EITHER a part_id OR a slot (JOB_AD, CV, CV_A, CV_B, CONTEXT, ITEM)

Assembly of one condition x variant (``PromptTemplate.render``):

* steps run in order; parts with role ``system`` form the system message, every
  other step the user message;
* consecutive steps of one message are separated by a blank line, except that a
  SLOT is placed on the line directly below the step before it (so the header
  ``JOB ADVERTISEMENT`` is followed on the next line by the job ad);
* slot values: JOB_AD = the job ad (stimuli/jobs.csv) localized to the base city
  of the CV(s); CV / CV_A / CV_B = the rendered CV clone(s); CONTEXT = the probe
  context part for the trial (``probe_context_generic`` or
  ``probe_context_occupation`` with ``{title}`` = the job title); ITEM = the item
  text of prompts/principle_items.csv in double quotes.

Versions: a template's ``user_template`` is the assembled user message with each
slot shown as ``{SLOT}``; ``version`` = ``<template_id>@sha256:<sha256 of
user_template>``. The system message's version is ``system@sha256:<sha256 of its
text>``. Template ids: ``<condition>_<variant>`` and ``principle_probe``.

The validator (``validate_library``) checks the structure: required recipes,
consecutive steps, known parts and slots, task/variant consistency, one system
part shared by every recipe, required slots per task, the output instructions as
the last step and identical across the wording variants of a task, and that each
neutrality recipe equals its baseline recipe plus exactly one added step: the
intervention part, immediately before the output instructions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import csvio
from .config import JobAd
from .utils import normalize_newlines, sha256_text, stable_json

SYSTEM_TEMPLATE_ID = "system"
PRINCIPLE_TEMPLATE_ID = "principle_probe"
TASK_CONDITIONS = ("baseline", "neutrality", "forced_choice", "forced_choice_neutrality")
ALL_CONDITIONS = (*TASK_CONDITIONS, "principle_probe")
DEFAULT_VARIANTS = ("k1", "k2", "k3")
TASKS = ("independent", "forced_choice", "principle_probe")
CONDITION_TASK = {"baseline": "independent", "neutrality": "independent", "forced_choice": "forced_choice",
                  "forced_choice_neutrality": "forced_choice", "principle_probe": "principle_probe"}
INTERVENTION_PAIRS = (("baseline", "neutrality"), ("forced_choice", "forced_choice_neutrality"))
ROLES = ("system", "user")
PART_TYPES = ("system", "intro", "section_header", "task_instruction", "intervention", "output_format",
              "probe_context", "probe_question")
SLOTS = ("JOB_AD", "CV", "CV_A", "CV_B", "CONTEXT", "ITEM")
SLOTS_BY_TASK = {"independent": ("JOB_AD", "CV"), "forced_choice": ("JOB_AD", "CV_A", "CV_B"),
                 "principle_probe": ("CONTEXT", "ITEM")}
# the part type that must directly precede each slot (CONTEXT opens the user message)
SLOT_AFTER = {"JOB_AD": "section_header", "CV": "section_header", "CV_A": "section_header",
              "CV_B": "section_header", "ITEM": "probe_question", "CONTEXT": None}
PLACEHOLDERS_BY_PART_TYPE = {"probe_context": {"title"}}
PROBE_CONTEXT_GENERIC = "probe_context_generic"
PROBE_CONTEXT_OCCUPATION = "probe_context_occupation"

# The single paragraph that distinguishes the neutrality conditions (contract, section 4).
# The intervention part of prompts/prompt_parts.csv must equal it (checked); the mock
# provider recognises the neutrality conditions by it.
NEUTRALITY_PARAGRAPH = (
    "National origin and nationality are not job-relevant selection criteria. Do not use them "
    "directly or indirectly in your assessment. Base the decision only on job-relevant "
    "qualifications, skills and experience."
)
PSEUDONYMISATION_SENTENCE = ("Applications in this screening system are pseudonymised: names and contact "
                             "details are replaced by an applicant reference.")
OUTPUT_PARAGRAPH_PREFIX = "Respond with a single JSON object"
PARTS_COLUMNS = ("part_id", "role", "part_type", "task", "variant", "text")
RECIPE_COLUMNS = ("condition", "task", "variant", "step", "part_id", "slot")
_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


class PromptError(ValueError):
    """The prompt tables cannot be read or assembled."""


def template_id(condition: str, variant: str | None) -> str:
    return PRINCIPLE_TEMPLATE_ID if condition == "principle_probe" else f"{condition}_{variant}"


# --------------------------------------------------------------------------- #
# data classes
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PromptPart:
    part_id: str
    role: str
    part_type: str
    tasks: tuple[str, ...]          # ("all",) or task names
    variant: str | None
    text: str

    def used_by(self, task: str) -> bool:
        return "all" in self.tasks or task in self.tasks


@dataclass(frozen=True)
class RecipeStep:
    step: int
    part_id: str | None = None
    slot: str | None = None

    @property
    def label(self) -> str:
        return self.part_id if self.part_id else f"[{self.slot}]"


def slot_text(slot: str, value: str) -> str:
    """How a slot value appears in the prompt (ITEM is quoted)."""
    return f'"{value}"' if slot == "ITEM" else value


@dataclass(frozen=True)
class PromptTemplate:
    """One condition x wording variant, assembled from its recipe."""

    template_id: str
    condition: str
    task: str
    variant: str | None
    steps: tuple[RecipeStep, ...]
    parts: dict[str, PromptPart] = field(repr=False, compare=False)

    def assemble(self, values: dict[str, str]) -> tuple[str, str]:
        """(system text, user text) with the slot ``values`` inserted."""
        chunks: dict[str, list[str]] = {"system": [], "user": []}
        for s in self.steps:
            if s.part_id:
                part = self.parts[s.part_id]
                chunks[part.role].append(part.text)
                continue
            if s.slot not in values:
                raise PromptError(f"{self.template_id}: no value for slot {s.slot}")
            target = chunks["user"]
            value = slot_text(s.slot, values[s.slot])
            if target:
                target[-1] = f"{target[-1]}\n{value}"
            else:
                target.append(value)
        return "\n\n".join(chunks["system"]), "\n\n".join(chunks["user"])

    @property
    def slots(self) -> list[str]:
        return [s.slot for s in self.steps if s.slot]

    @property
    def system_text(self) -> str:
        return self.assemble({k: "" for k in self.slots})[0]

    @property
    def user_template(self) -> str:
        """The user message with every slot shown as ``{SLOT}``."""
        return self.assemble({k: "{" + k + "}" for k in self.slots})[1]

    @property
    def sha256(self) -> str:
        return sha256_text(self.user_template)

    @property
    def version(self) -> str:
        return f"{self.template_id}@sha256:{self.sha256}"

    def render(self, values: dict[str, str]) -> list[dict]:
        system, user = self.assemble(values)
        return build_messages(system, user)


@dataclass(frozen=True)
class PromptLibrary:
    parts: dict[str, PromptPart]
    templates: dict[str, PromptTemplate]      # template_id -> template

    def template(self, tid: str) -> PromptTemplate:
        try:
            return self.templates[tid]
        except KeyError as e:
            raise PromptError(f"no recipe for template {tid!r} in prompts/prompt_recipes.csv") from e

    @property
    def system_part(self) -> PromptPart:
        ids = {s.part_id for t in self.templates.values() for s in t.steps
               if s.part_id and self.parts[s.part_id].role == "system"}
        if len(ids) != 1:
            raise PromptError(f"every recipe must use the same single system part, found {sorted(ids)}")
        return self.parts[ids.pop()]

    @property
    def system_text(self) -> str:
        return self.system_part.text

    @property
    def system_sha256(self) -> str:
        return sha256_text(self.system_text)

    @property
    def system_version(self) -> str:
        return f"{SYSTEM_TEMPLATE_ID}@sha256:{self.system_sha256}"

    def texts_for_scan(self) -> dict[str, str]:
        """Every assembled template (slots as ``{SLOT}``) and the system prompt, for the leak scan."""
        out = {SYSTEM_TEMPLATE_ID: self.system_text}
        out.update({tid: t.user_template for tid, t in self.templates.items()})
        return out


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #
def load_parts(path: str | Path) -> dict[str, PromptPart]:
    rows = csvio.read_rows(path, PARTS_COLUMNS, allowed=PARTS_COLUMNS)
    parts: dict[str, PromptPart] = {}
    for r in rows:
        pid = csvio.text(r["part_id"])
        if not pid:
            raise PromptError(f"{Path(path).name}: a row has no part_id")
        if pid in parts:
            raise PromptError(f"{Path(path).name}: duplicate part_id {pid!r}")
        tasks = tuple(csvio.items(r["task"])) or ("",)
        parts[pid] = PromptPart(part_id=pid, role=csvio.text(r["role"]), part_type=csvio.text(r["part_type"]),
                                tasks=tasks, variant=csvio.optional(r["variant"]),
                                text=normalize_newlines(r["text"] or "").strip())
    return parts


def load_recipes(path: str | Path, parts: dict[str, PromptPart]) -> dict[str, PromptTemplate]:
    rows = csvio.read_rows(path, RECIPE_COLUMNS, allowed=RECIPE_COLUMNS)
    grouped: dict[tuple[str, str, str | None], list[RecipeStep]] = {}
    for r in rows:
        cond, task, variant = csvio.text(r["condition"]), csvio.text(r["task"]), csvio.optional(r["variant"])
        at = csvio.where(path, f"{cond} {variant or ''} step {r['step']}")
        step = RecipeStep(csvio.integer(r["step"], at), csvio.optional(r["part_id"]), csvio.optional(r["slot"]))
        grouped.setdefault((cond, task, variant), []).append(step)
    templates: dict[str, PromptTemplate] = {}
    for (cond, task, variant), steps in grouped.items():
        tid = template_id(cond, variant)
        if tid in templates:
            raise PromptError(f"{Path(path).name}: recipe {tid} is listed with two different tasks")
        templates[tid] = PromptTemplate(tid, cond, task, variant, tuple(sorted(steps, key=lambda s: s.step)),
                                        parts)
    return templates


def load_library(prompts_dir: str | Path) -> PromptLibrary:
    d = Path(prompts_dir)
    parts = load_parts(d / "prompt_parts.csv")
    return PromptLibrary(parts, load_recipes(d / "prompt_recipes.csv", parts))


# --------------------------------------------------------------------------- #
# rendering helpers
# --------------------------------------------------------------------------- #
def render_job_ad(job: JobAd) -> str:
    """Render a LOCALIZED job ad (``JobAd.localize(city, country)``: the ad is located
    in the base city of the CV it is shown with)."""
    lines = [
        f"Position: {job.title}",
        f"Employer: {job.employer}",
        f"Location: {job.location}",
        "",
        "About us:",
        job.about.strip(),
        "",
        "Your tasks:",
        *[f"- {t}" for t in job.tasks],
        "",
        "Your profile:",
        *[f"- {r}" for r in job.requirements],
        "",
        "What we offer:",
        *[f"- {o}" for o in job.offer],
    ]
    text = "\n".join(lines)
    if "{city}" in text or "{country}" in text:
        raise ValueError(f"job ad {job.id} is not localized (call JobAd.localize(city, country) first)")
    return text


def render_independent(template: PromptTemplate, job: JobAd, cv_text: str) -> str:
    """The user message of an independent-evaluation template."""
    return template.assemble({"JOB_AD": render_job_ad(job), "CV": cv_text.rstrip("\n")})[1]


def render_forced_choice(template: PromptTemplate, job: JobAd, cv_a: str, cv_b: str) -> str:
    """The user message of a forced-choice template (``cv_a`` is candidate A)."""
    return template.assemble({"JOB_AD": render_job_ad(job), "CV_A": cv_a.rstrip("\n"),
                              "CV_B": cv_b.rstrip("\n")})[1]


def render_principle(template: PromptTemplate, context_text: str, statement: str) -> str:
    """The user message of the principle probe."""
    return template.assemble({"CONTEXT": context_text, "ITEM": statement})[1]


def build_messages(system_text: str, user_text: str) -> list[dict]:
    return [{"role": "system", "content": system_text.rstrip("\n")}, {"role": "user", "content": user_text}]


def prompt_sha256(messages: list[dict]) -> str:
    return sha256_text(stable_json(messages))


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def paragraphs(text: str) -> list[str]:
    return normalize_newlines(text).strip("\n").split("\n\n")


def check_intervention(base_text: str, treated_text: str) -> list[str]:
    """Problems (empty = OK) on ASSEMBLED texts: ``treated`` must be ``base`` plus
    exactly one paragraph, equal to NEUTRALITY_PARAGRAPH, immediately before the
    output instructions. (The structural check on the recipes is in
    ``check_recipe_intervention``; this one guards the assembled result.)"""
    problems: list[str] = []
    bp, tp = paragraphs(base_text), paragraphs(treated_text)
    if len(tp) != len(bp) + 1:
        return [f"expected exactly one extra paragraph, got {len(tp) - len(bp)}"]
    inserted = [i for i in range(len(tp)) if tp[:i] + tp[i + 1:] == bp]
    if not inserted:
        return ["treated prompt is not the base prompt plus one inserted paragraph (other text differs)"]
    idx = inserted[0]
    if tp[idx] != NEUTRALITY_PARAGRAPH:
        problems.append("inserted paragraph does not match the canonical neutrality paragraph")
    out_idx = [i for i, p in enumerate(bp) if p.startswith(OUTPUT_PARAGRAPH_PREFIX)]
    if len(out_idx) != 1:
        problems.append("base prompt must contain exactly one output-instruction paragraph")
    elif idx != out_idx[0]:
        problems.append(f"neutrality paragraph inserted at position {idx}, expected {out_idx[0]} "
                        "(immediately before the output instructions)")
    return problems


def check_recipe_intervention(base: PromptTemplate, treated: PromptTemplate) -> list[str]:
    """Structural check: ``treated`` = ``base`` plus exactly ONE added step, which is an
    intervention part, inserted immediately before the output-instruction step."""
    b = [s.label for s in base.steps]
    t = [s.label for s in treated.steps]
    if len(t) != len(b) + 1:
        return [f"must have exactly one step more than {base.template_id} (has {len(t) - len(b):+d})"]
    added = [i for i in range(len(t)) if t[:i] + t[i + 1:] == b]
    if not added:
        return [f"is not {base.template_id} plus one added step (other steps differ)"]
    i = added[0]
    part = treated.parts.get(t[i])
    problems = []
    if part is None or part.part_type != "intervention":
        problems.append(f"the added step {t[i]!r} is not an intervention part")
    if i + 1 >= len(t) or treated.parts.get(t[i + 1]) is None or treated.parts[t[i + 1]].part_type != "output_format":
        problems.append("the intervention must come immediately before the output instructions")
    return problems


def required_template_ids(variants=DEFAULT_VARIANTS) -> list[str]:
    return [template_id(c, k) for c in TASK_CONDITIONS for k in variants] + [PRINCIPLE_TEMPLATE_ID]


def _check_parts(parts: dict[str, PromptPart]) -> list[str]:
    problems = []
    for p in parts.values():
        at = f"part {p.part_id}"
        if p.role not in ROLES:
            problems.append(f"{at}: role must be one of {ROLES}, got {p.role!r}")
        if p.part_type not in PART_TYPES:
            problems.append(f"{at}: part_type must be one of {PART_TYPES}, got {p.part_type!r}")
        if (p.role == "system") != (p.part_type == "system"):
            problems.append(f"{at}: role 'system' iff part_type 'system'")
        if not set(p.tasks) <= {*TASKS, "all"} or ("all" in p.tasks and len(p.tasks) > 1):
            problems.append(f"{at}: task must be 'all' or a ' | '-list of {TASKS}, got {' | '.join(p.tasks)!r}")
        if p.variant is not None and p.variant not in DEFAULT_VARIANTS:
            problems.append(f"{at}: variant must be empty or one of {DEFAULT_VARIANTS}")
        if not p.text:
            problems.append(f"{at}: empty text")
        allowed = PLACEHOLDERS_BY_PART_TYPE.get(p.part_type, set())
        bad = sorted(set(_PLACEHOLDER_RE.findall(p.text)) - allowed)
        if bad:
            problems.append(f"{at}: unknown placeholder(s) {bad} (allowed here: {sorted(allowed) or 'none'})")
        if p.part_type == "intervention" and p.text != NEUTRALITY_PARAGRAPH:
            problems.append(f"{at}: the intervention text differs from the canonical neutrality paragraph "
                            f"(design contract, section 4)")
    for pid in (PROBE_CONTEXT_GENERIC, PROBE_CONTEXT_OCCUPATION):
        if pid not in parts or parts[pid].part_type != "probe_context":
            problems.append(f"part {pid} (part_type probe_context) is missing")
    if PROBE_CONTEXT_OCCUPATION in parts and "{title}" not in parts[PROBE_CONTEXT_OCCUPATION].text:
        problems.append(f"part {PROBE_CONTEXT_OCCUPATION}: must contain {{title}}")
    return problems


def _check_recipe(t: PromptTemplate) -> list[str]:
    at = f"recipe {t.template_id}"
    problems = []
    if t.condition not in ALL_CONDITIONS:
        return [f"{at}: unknown condition {t.condition!r}"]
    if t.task != CONDITION_TASK[t.condition]:
        problems.append(f"{at}: task must be {CONDITION_TASK[t.condition]!r} for condition {t.condition}")
    if [s.step for s in t.steps] != list(range(1, len(t.steps) + 1)):
        problems.append(f"{at}: steps must be numbered 1..n without gaps or repeats")
    for s in t.steps:
        if bool(s.part_id) == bool(s.slot):
            problems.append(f"{at} step {s.step}: give exactly one of part_id or slot")
        elif s.part_id and s.part_id not in t.parts:
            problems.append(f"{at} step {s.step}: unknown part_id {s.part_id!r}")
        elif s.slot and s.slot not in SLOTS:
            problems.append(f"{at} step {s.step}: unknown slot {s.slot!r} (slots: {SLOTS})")
    if problems:
        return problems
    parts = [t.parts[s.part_id] for s in t.steps if s.part_id]
    for p in parts:
        if not p.used_by(t.task):
            problems.append(f"{at}: part {p.part_id} is written for task {' | '.join(p.tasks)}, not {t.task}")
        if p.variant is not None and p.variant != t.variant:
            problems.append(f"{at}: part {p.part_id} belongs to variant {p.variant}, not {t.variant}")
        if p.part_type == "probe_context":
            problems.append(f"{at}: probe contexts enter through the CONTEXT slot, not as a step")
    system_steps = [i for i, s in enumerate(t.steps) if s.part_id and t.parts[s.part_id].role == "system"]
    if system_steps != [0]:
        problems.append(f"{at}: step 1 must be the system part, and it must be the only system step")
    slots = t.slots
    if sorted(slots) != sorted(SLOTS_BY_TASK[t.task]):
        problems.append(f"{at}: task {t.task} needs the slots {SLOTS_BY_TASK[t.task]} exactly once each, has {slots}")
    if t.task == "forced_choice" and "CV_A" in slots and "CV_B" in slots and slots.index("CV_A") > slots.index("CV_B"):
        problems.append(f"{at}: CV_A must come before CV_B")
    user = [s for s in t.steps if not (s.part_id and t.parts[s.part_id].role == "system")]
    for i, s in enumerate(user):
        if not s.slot:
            continue
        need = SLOT_AFTER[s.slot]
        prev = t.parts.get(user[i - 1].part_id) if i > 0 and user[i - 1].part_id else None
        if need is None and i != 0:
            problems.append(f"{at}: slot {s.slot} must open the user message")
        if need is not None and (prev is None or prev.part_type != need):
            problems.append(f"{at}: slot {s.slot} must directly follow a {need} part")
    outs = [i for i, s in enumerate(t.steps) if s.part_id and t.parts[s.part_id].part_type == "output_format"]
    if outs != [len(t.steps) - 1]:
        problems.append(f"{at}: exactly one output_format part, as the last step")
    has_intervention = any(p.part_type == "intervention" for p in parts)
    if has_intervention and t.condition not in {tr for _, tr in INTERVENTION_PAIRS}:
        problems.append(f"{at}: contains an intervention part but is not a neutrality condition")
    return problems


def validate_library(lib: PromptLibrary, variants=DEFAULT_VARIANTS) -> list[str]:
    """Structural checks of the prompt tables (see the module docstring)."""
    problems = _check_parts(lib.parts)
    for tid in required_template_ids(variants):
        if tid not in lib.templates:
            problems.append(f"recipe {tid} is missing from prompts/prompt_recipes.csv")
    recipe_problems = {tid: _check_recipe(t) for tid, t in lib.templates.items()}
    for ps in recipe_problems.values():
        problems += ps
    if any(recipe_problems.values()):
        return problems
    try:
        system = lib.system_part
    except PromptError as e:
        return problems + [str(e)]
    if PSEUDONYMISATION_SENTENCE not in system.text:
        problems.append("system prompt lacks the constant pseudonymisation sentence (A23)")
    for k in variants:
        for base, treated in INTERVENTION_PAIRS:
            b, t = lib.templates.get(template_id(base, k)), lib.templates.get(template_id(treated, k))
            if b is None or t is None:
                continue
            problems += [f"recipe {t.template_id}: {p}" for p in check_recipe_intervention(b, t)]
            problems += [f"{t.template_id} vs {b.template_id}: {p}"
                         for p in check_intervention(b.user_template, t.user_template)]
    for cond in TASK_CONDITIONS:
        ts = [lib.templates[template_id(cond, k)] for k in variants if template_id(cond, k) in lib.templates]
        if len({t.steps[-1].part_id for t in ts}) > 1:
            problems.append(f"{cond}: wording variants must share the identical output-instruction part")
        if len({t.user_template for t in ts}) != len(ts):
            problems.append(f"{cond}: wording variants must differ in wording")
    return problems


def validate_prompts(prompts_dir: str | Path, variants=DEFAULT_VARIANTS) -> list[str]:
    """Load prompts/prompt_parts.csv and prompts/prompt_recipes.csv and validate them."""
    try:
        lib = load_library(prompts_dir)
    except (csvio.TableError, PromptError) as e:
        return [str(e)]
    return validate_library(lib, variants)
