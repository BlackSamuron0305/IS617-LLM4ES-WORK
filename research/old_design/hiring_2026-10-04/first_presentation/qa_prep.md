# Pitch: question-and-answer preparation

Internal notes for the 5 minutes of questions on 13.10.2026. **Facts and pointers, not
answers to read out.** Every member should be able to answer every question in their own
words. AI-assisted (Claude Code, 2026-10-04).

"Open" marks something the team has not decided. Decide it before the pitch, or say
plainly that it is open.

## The question and why it matters

**1. LLMs are already known to be biased against Arabs and Muslims. What is new?**

- On slide 2: Abid et al. 2021, GPT-3, 66 of 100 completions of "Two Muslims walked into
  a" are violent (a religion, not a nationality). Lippens 2024: GPT-3.5, one pooled "Arab"
  group signalled by names, -1.41 points on a 1-100 score.
- Every study pools. We found no study in which an LLM makes a hiring decision and national
  origin varies across more than one Arab country (searches of 29-30.09 and 04.10.2026).
- Not claimed as new: that LLMs penalise Arab applicants; that LLMs tell Arab countries
  apart in general; that origin matters in human hiring.
- The claim is tentative. Say "to our knowledge". One paper is not read in full
  (Bilon 2025: its abstract reports only U.S. vs non-U.S.). No Arabic-language database
  was searched.
- Source: `research/novelty_assessment.md` sections 3 to 5.

**2. Your motivation is bias against Muslims, but you study Arab nationalities. Is that
the same thing?**

- No, and do not claim it. Most Muslims are not Arab, and our CVs state no religion.
- The link: the Arab League countries are majority-Muslim, and models bring up religion
  when they describe Middle Eastern people (Cheng, Durmus & Jurafsky 2023; GPT-3.5 and
  GPT-4). So a bias against Muslims can be expected to reach Arab nationalities.
- Abid et al. 2021 is about religion, on GPT-3. The paper does not mention Arabs,
  nationality or country.
- What we measure: how nationalities are treated, not bias against Islam.
- Turkish and Maldivian are Muslim-majority and not Arab. Open: whether the analysis uses
  them to tell religion from Arab origin. No analysis plan exists yet.

**3. That evidence is from old models. Do newer models still show a penalty?**

- Say it is open. Abid et al. 2021: GPT-3, a model of 2020. Hemmatian et al. 2023: a
  weaker form in later GPT models. Shieh et al. 2026: models of 2023.
- Evidence against a penalty in newer models. The team took the first two off the slides
  and out of the proposal on 2026-10-04, so expect to be asked about them:
  - Hoffmann et al. 2026 (preprint): Gemini 2.0 Flash, pooled Arabic-sounding male names,
    about zero.
  - Arcuschin et al. 2026: in hiring, loan and admission tasks every detected race or
    ethnicity bias favoured the minority group (21 to 0).
  - Bunel et al. 2026 (working paper): 18 LLMs recommend less discrimination against a
    real origin (Moroccan) than against a fictional group.
- Our design answers it: the German, Turkish and not-stated conditions show whether the
  disadvantage appears in our four models. The main question, differences among the 22,
  holds in either direction.
- A pooled average near zero does not show that the nationalities are treated alike:
  differences between them are averaged away. That is a possibility, not a finding.

**4. Why hiring and promotion?**

- They are the measuring tool, not the claim. To compare 22 nationalities we need a task
  in which the nationality can change while everything else stays the same, and in which
  the model answers with a number. A CV does this.
- It is how discrimination is usually measured: among employers with correspondence
  experiments (Lippens, Vermeiren & Baert 2023), in LLMs with CV audits (Gaebler et al.
  2024; Armstrong et al. 2024).
- It is also a realistic case in the Arab world (question 7).

**5. Isn't the result predictable? A known penalty, plus models that tell countries
apart, plus noise.**

- This is the strongest objection (`research/novelty_assessment.md` section 6).
- MENAValues (Zahraei et al. 2025) is about values, not about decisions on a person with
  qualifications held fixed.
- Any set of nationality labels makes scores spread a little. The 4 placebo nationalities
  show how large that spread is for unrelated countries.
- Open: the exact rule for "more spread than the placebo set" is not written for the
  current design.

**6. What if you find no differences?**

- Then one category is adequate for these models. That is an answer, not a failure.
- Human evidence inside the Arab world leans that way: Qatari citizens make no significant
  distinction between nationalities (Shockley & Gengler 2024; outcome is residency, not
  hiring); Arab expatriates in Kuwait and Qatar favour "fellow Arabs" as one group
  (Blaydes & Gengler 2023; attitudes, not hiring).

**7. Why does this matter outside the course?**

- LLM recruiting tools are being built for this market. Albaroudi et al. 2026: CV matching
  for the Saudi market on Llama 3.1; 18 Arab nationalities in the data, coded Arab vs
  non-Arab.
- Nationality openly sorts workers in these labour markets. Jordan: Razzaz 2017 (ILO
  report). Qatar, low-income workers: Egyptian QR1,454 vs Nepali QR853 a month, plain
  averages without controls (Gardner et al. 2013). Gulf states expelled workers by Arab
  nationality in 1990-91 (Kapiszewski 2006, a UN paper).
- Careful: most of this compares Arab with Asian or Western workers, or is state policy.
  Differences among Arab nationalities at equal qualifications are barely studied.

## The design

**8. Why a nationality line and not names?**

- A name signals "Arab" as one group. It cannot tell the 22 countries apart.
- A name adds signals we do not want: gender, religion, sometimes region.
- The same name would sit next to a non-Arab nationality on some versions: a mixed signal.
- A missing name is not neutral either, so the main prompt says applications are
  pseudonymised.
- Source: the note "why the CVs carry no names" in `paper/final_paper/paper.tex`.

**9. Is a nationality line on a CV realistic?**

- The setting is the Arab world, where nationality openly sorts workers (question 7).
- Open: we have no checked source on how common the line is on real CVs there. Find one
  or say so.

**10. Why are the jobs set in Arab countries?**

- The setting moved from Germany to the Arab world on 2026-10-01. Every job is run once in
  each of the 22 Arab League countries.
- The human field experiments on Arab names are all from Western labour markets. Do not
  present that gap as evidence about Arab labour markets.

**11. Won't a model simply prefer locals?**

- Possible. `host_national` marks runs where the nationality equals the country of the
  job, so that case can be looked at separately.
- Several Gulf states favour citizens in hiring by policy. A model that prefers host
  nationals may be reproducing that (`ETHICS.md` section 4; the legal details there are
  marked as unverified, do not cite them).

**12. Why Comoros, Djibouti and Somalia?**

- They are Arab League members whose Arab identity is contested. They are flagged, stay in
  every comparison, and are pointed out in the paper.
- Arab League membership is a political-institutional criterion, not an ethnic one.

**13. Why these four models? Why not GPT or Claude?**

- No API budget. Open-weight models run on bwUniCluster with vLLM.
- Pinned open models can be re-run by others. The course asks for 3 to 5 models.
- Limit: models of 8 to 24 billion parameters. Results say nothing about larger
  commercial models.

**14. Only English?**

- Yes. Jobs require English only and every CV lists English (C1) only. Arabic and German
  prompts are parked.

**15. One CV per job and one run per combination. How do you tell signal from noise?**

- Each nationality is rated in 440 job-country combinations per model.
- Three wordings rotate, so a result does not hang on one phrasing.
- The placebo set gives the spread that labels cause in general.
- Open: sampling settings and the analysis plan.

**16. What are your hypotheses? How will you analyse the answers?**

- Open, and say so: hypotheses and the analysis plan for this design are not written.
  They are written before the first real run, not after seeing results. Confirmatory and
  exploratory analyses stay separate.

**17. Why a "lottery" answer in the choice between two?**

- Version 1 allows A, B or lottery. Version 2 allows only A or B.
- Both candidates have the same CV. (Reading by Claude, check it: lottery is then the
  answer that does not use nationality, and version 2 shows what happens when the model
  must pick.)

**18. Why promotion as well as hiring?**

- Added by the team on 2026-10-04. Same job text and CV, only the framing differs.
- Open: the team's reason is not written down. It is block 4, the lowest priority.

## Feasibility

**19. 128,480 runs per model. Is that realistic?**

- Blocks are ordered by priority and each is a complete result. Block 1 is 12,760 runs per
  model (51,040 for four models) and is enough for the midterm.
- Runs go in small batches. A timing test of a few hundred runs comes first.
- Laith has run more than 800,000 calls in 3 to 4 days before, in small batches.
- If time runs out, block 4 is dropped first. The paper states what was run.

## Ethics and AI use

**20. Can this stigmatise a country?**

- A difference between two labels is evidence about the model, never about people from
  those countries. Every version of a CV is equally qualified.
- No ranking of countries without uncertainty intervals. A null result gets the same
  weight as a disparity (`ETHICS.md` sections 3 and 6).

**21. Could someone use this as a hiring tool?**

- It is an audit. Code, prompts and outputs must not be used to screen real applicants
  (`ETHICS.md` section 2).

**22. Did you use AI for this project?**

- Yes, and it is declared per task. Claude Code assisted with the literature search and
  research notes, the design documents, the prompts, the job ads and CVs, the repository,
  and the draft of these slides.
- All sources on the slides were read in full text; the team checks each number against
  the source.
