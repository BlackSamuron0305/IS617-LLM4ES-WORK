"""Deterministic mock provider with a transparent generative model.

The mock sees ONLY the prompt text, exactly like a real model: it reads the
``Nationality:`` and ``Applicant reference:`` lines, the stated experience in the
profile and whether the EDUCATION section still lists a qualification. For
principle probes it reads the statement and looks it up among the configured
items. It never receives trial metadata.

Generative model (all nationality effects SYNTHETIC; default zero):

independent evaluation
    latent = intercept + years_slope * years - q * missing_qualification + u_cv + s * e_nat + noise
    u_cv   ~ Normal(0, cv_sd), fixed per applicant reference (hash-seeded)
    e_nat  = configured synthetic effect of the stated nationality (NONE if absent)
    s      = 1 - neutrality_shrink if the neutrality paragraph is in the prompt, else 1
    noise  ~ Normal(0, noise_sd), drawn from the call SEED only, so clones that share
             a seed (A17) share the noise draw (common random numbers)
    overall_fit = clip(round(latent), 0, 100); interview = "yes" if latent + N(0, 3) >= threshold

forced choice
    P(choose A) = logistic((util_A - util_B) / fc_scale + position_bias)

principle probe
    endorses neutrality with probability principle_endorse_prob (answer = yes for
    pro-keyed, no for reverse-keyed items); control items get their expected
    answer with probability 0.9

Failure injection (MockCfg.rates) produces API errors, empty output, refusals,
malformed JSON, schema violations, code fences and leading prose; its random
draw depends on seed, prompt and attempt number, so retried transport errors
can succeed. Same prompt + seed + attempt -> identical output.
"""

from __future__ import annotations

import json
import math
import random
import re
import threading
import time
from collections import Counter

from ..config import MockCfg, ModelSpec, PrincipleSpec
from ..prompts import NEUTRALITY_PARAGRAPH
from ..utils import derive_int, sha256_text
from .base import ChatRequest, ChatResponse, NonRetryableProviderError, Provider, RetryableProviderError

_NAT_RE = re.compile(r"^Nationality: (.+)$", re.MULTILINE)
_REF_RE = re.compile(r"^Applicant reference: (APP-\d+)$", re.MULTILINE)
_EXP_RE = re.compile(r"(\d+) (years?|months)")
_QUAL_LINE_RE = re.compile(r"^\d{4} - \d{4} \| ", re.MULTILINE)
_STATEMENT_RE = re.compile(r'Consider the following statement:\n"(.+)"')

REFUSAL_TEXT = ("I'm sorry, but I can't help with ranking or evaluating individual job applicants "
                "in this way.")
_REASONS_INDEPENDENT = (
    "The applicant's experience matches the core requirements of the position.",
    "Relevant experience and skills; the language requirements are met.",
    "Some requirements are met, but the relevant experience is limited.",
    "Solid profile with the required skills and an unrestricted work authorization.",
)
_REASONS_FC = (
    "Candidate {c} has more relevant experience for this role.",
    "Both are suitable; candidate {c} covers the requirements slightly better.",
)
_REASONS_PRINCIPLE = (
    "Selection should depend on job-relevant qualifications.",
    "This follows from basing decisions on skills and experience.",
)


def nationality_effects(cfg: MockCfg, codes: list[str]) -> dict[str, float]:
    """Resolve the configured SYNTHETIC effects (explicit values override the pattern)."""
    eff = {c: 0.0 for c in codes}
    if cfg.effect_pattern == "alphabetical_ramp" and len(codes) > 1:
        ordered = sorted(codes)
        for i, c in enumerate(ordered):
            eff[c] = cfg.effect_amplitude * (i / (len(ordered) - 1) - 0.5)
    eff.update(cfg.nationality_effects)
    return eff


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _clip(x: float, lo: int = 0, hi: int = 100) -> int:
    return int(max(lo, min(hi, round(x))))


class MockProvider(Provider):
    name = "mock"
    is_mock = True

    def __init__(self, spec: ModelSpec, cfg: MockCfg, demonym_to_code: dict[str, str], codes: list[str],
                 principle: PrincipleSpec | None = None):
        super().__init__(spec)
        self.cfg = cfg
        self.demonym_to_code = demonym_to_code
        self.effects = nationality_effects(cfg, codes)
        self.items = {i.text: i for i in principle.items} if principle else {}
        self._attempts: Counter = Counter()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # reading the prompt (what a real model would see)
    # ------------------------------------------------------------------ #
    def _read_cv(self, block: str) -> dict:
        nat = _NAT_RE.search(block)
        ref = _REF_RE.search(block)
        profile = block.split("PROFILE", 1)[1] if "PROFILE" in block else block
        exp = _EXP_RE.search(profile)
        years = 3.0
        if exp:
            years = float(exp.group(1)) / (12.0 if exp.group(2) == "months" else 1.0)
        education = block.split("EDUCATION", 1)[1].split("SKILLS", 1)[0] if "EDUCATION" in block else ""
        demonym = nat.group(1).strip() if nat else None
        code = "NONE" if demonym is None else self.demonym_to_code.get(demonym, "UNKNOWN")
        return {"code": code, "ref": ref.group(1) if ref else "APP-0000", "years": years,
                "missing_qualification": _QUAL_LINE_RE.search(education) is None}

    def _cv_effect(self, ref: str) -> float:
        return random.Random(derive_int("mock-cv", ref)).gauss(0.0, self.cfg.cv_sd)

    def _utility(self, cv: dict, shrink: float) -> float:
        return (self.cfg.years_slope * cv["years"] + self._cv_effect(cv["ref"])
                - self.cfg.qualification_effect * cv["missing_qualification"]
                + shrink * self.effects.get(cv["code"], 0.0))

    # ------------------------------------------------------------------ #
    def complete(self, request: ChatRequest) -> ChatResponse:
        t0 = time.perf_counter()
        prompt = request.system_text + "\n\n" + request.user_text
        key = sha256_text(f"{request.seed}|{prompt}")
        with self._lock:
            attempt = self._attempts[key]
            self._attempts[key] += 1
        fail_rng = random.Random(derive_int("mock-fail", key, attempt))
        sample_rng = random.Random(derive_int("mock-sample", request.seed, request.temperature))
        rates = self.cfg.rates

        u = fail_rng.random()
        if u < rates.api_error_fatal:
            raise NonRetryableProviderError("mock: synthetic non-retryable API error (HTTP 400)", status_code=400)
        if u < rates.api_error_fatal + rates.api_error_retryable:
            raise RetryableProviderError("mock: synthetic transient API error (HTTP 503)", status_code=503)

        user = request.user_text
        shrink = (1.0 - self.cfg.neutrality_shrink) if NEUTRALITY_PARAGRAPH in user else 1.0
        if "CANDIDATE A" in user and "CANDIDATE B" in user:
            task = "forced_choice"
            body = self._forced_choice(user, shrink, sample_rng)
        elif "APPLICANT CV" in user:
            task = "independent"
            body = self._independent(user, shrink, sample_rng, request.temperature)
        else:
            task = "principle_probe"
            body = self._principle(user, sample_rng)

        text, injected = self._format(body, task, fail_rng)
        latency = (time.perf_counter() - t0) * 1000.0
        usage = {"prompt_tokens": len(prompt) // 4, "completion_tokens": len(text) // 4,
                 "total_tokens": (len(prompt) + len(text)) // 4, "estimated": True}
        return ChatResponse(
            text=text, finish_reason="stop", usage=usage, latency_ms=round(latency, 3), logprobs=None,
            raw_metadata={"mock_task": task, "mock_attempt": attempt, "mock_injected": injected,
                          "served_model": self.spec.model_id},
            request_params={"model": self.spec.model_id, "temperature": request.temperature,
                            "top_p": request.top_p, "max_tokens": request.max_tokens,
                            "seed": request.seed, "json_mode": request.json_mode},
        )

    # ------------------------------------------------------------------ #
    def _independent(self, user: str, shrink: float, rng: random.Random, temperature: float) -> dict:
        cv = self._read_cv(user.split("APPLICANT CV", 1)[1])
        c = self.cfg
        noise_scale = 1.0 if temperature > 0 else 0.0  # greedy decoding: no sampling noise
        latent = c.intercept + self._utility(cv, shrink) + noise_scale * rng.gauss(0.0, c.noise_sd)
        interview = "yes" if latent + noise_scale * rng.gauss(0.0, 3.0) >= c.interview_threshold else "no"
        return {
            "overall_fit": _clip(latent),
            "interview": interview,
            "confidence": _clip(60 + 0.8 * abs(latent - c.interview_threshold) + rng.gauss(0, 5)),
            "reason": rng.choice(_REASONS_INDEPENDENT),
        }

    def _forced_choice(self, user: str, shrink: float, rng: random.Random) -> dict:
        block_a, block_b = user.split("CANDIDATE A", 1)[1].split("CANDIDATE B", 1)
        a, b = self._read_cv(block_a), self._read_cv(block_b)
        p_a = _sigmoid((self._utility(a, shrink) - self._utility(b, shrink)) / self.cfg.fc_scale
                       + self.cfg.position_bias)
        choice = "A" if rng.random() < p_a else "B"
        p_chosen = p_a if choice == "A" else 1 - p_a
        return {"choice": choice, "confidence": _clip(50 + 80 * abs(p_chosen - 0.5) + rng.gauss(0, 5)),
                "reason": rng.choice(_REASONS_FC).format(c=choice)}

    def _principle(self, user: str, rng: random.Random) -> dict:
        m = _STATEMENT_RE.search(user)
        item = self.items.get(m.group(1)) if m else None
        if item is not None and item.keying == "control":
            answer = item.expected_answer if rng.random() < 0.9 else ("no" if item.expected_answer == "yes" else "yes")
        else:
            endorse = rng.random() < self.cfg.principle_endorse_prob
            reverse = item is not None and item.keying == "reverse"
            answer = "yes" if endorse != reverse else "no"
        return {"answer": answer, "agreement": _clip(rng.gauss(85, 8) if answer == "yes" else rng.gauss(20, 10)),
                "reason": rng.choice(_REASONS_PRINCIPLE)}

    # ------------------------------------------------------------------ #
    def _format(self, body: dict, task: str, rng: random.Random) -> tuple[str, str]:
        r = self.cfg.rates
        u = rng.random()
        acc = 0.0
        for name, rate in (("empty", r.empty), ("refusal", r.refusal), ("malformed_json", r.malformed_json),
                           ("schema_violation", r.schema_violation)):
            acc += rate
            if u < acc:
                if name == "empty":
                    return "", name
                if name == "refusal":
                    return REFUSAL_TEXT, name
                if name == "malformed_json":
                    return json.dumps(body)[:-7], name  # truncated, unterminated JSON
                bad = dict(body)
                if task == "independent":
                    bad["overall_fit"] = 150
                elif task == "forced_choice":
                    bad["choice"] = "both"
                else:
                    bad.pop("agreement")
                return json.dumps(bad), name
        text = json.dumps(body)
        injected = "clean"
        if rng.random() < r.code_fence:
            text = f"```json\n{text}\n```"
            injected = "code_fence"
        if rng.random() < r.leading_prose:
            text = "Here is my assessment:\n" + text
            injected = "leading_prose" if injected == "clean" else injected + "+leading_prose"
        return text, injected
