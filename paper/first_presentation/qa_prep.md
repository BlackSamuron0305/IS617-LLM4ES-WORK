# Q&A preparation for the pitch (visa design)

Written on 2026-10-10 by Claude Code. Facts and where they come from, not answers to
read out. Keys in backticks are in `research/literature_matrix.csv`. "Read" means the
text or data file itself was read; "tool" means the page was read through a summarising
tool and has to be checked before it is quoted; "press" is a press report. The research
notes behind all of this are in `research/visa_scenario/`.

## The short version

LLM bias among the Arab countries, with two questions.

1. Is there a bias? Two people hand in the same visa application, one with a Syrian and
   one with an Emirati passport, and the official rules are the same for both. Does a
   model rate them differently?
2. Can the countries be grouped into rich, normal and poor by how the models rate them?

## 1. Last week this was about banks, before that about hiring. Why visas now?

- In hiring, a nationality line can be removed before a model sees it. In a bank it
  cannot, but the passport hardly matters for a customer who lives in Germany.
- At a border the passport is the whole point, the stakes for the person are high, and
  automated tools that sort applicants by nationality have really existed (question 2).
- Honest: the topic changed three times. The design reuses the applicants, the models,
  the two-version guidance and the code of the bank design.

## 2. Do visa offices really use language models for this?

- No authority is documented as doing so. Say that plainly.
- What is documented is software that sorts or rates applicants, by fixed rules or by
  machine learning. Checked again on 2026-10-12: every quote below was compared with the
  document or page itself (slides 12 and 13 of `pitch_v5.pptx`).
  - United Kingdom, 2015 to 2020: "It streams applications 'Green' (low risk), 'Amber'
    (medium risk) or 'Red' (high risk)", with "a 'decision tree' approach with a series
    of yes/no questions". Visit applications in one office, early 2017: 96.36% of green
    issued, 48.59% of red (`icibi2017entry`, read). "nationality is one of the relevant
    factors used by the streaming tool"; stopped in August 2020 after a legal challenge
    (`ukhrb2020streaming`, read, a blog quoting a government letter;
    `foxglove2020visa`, a party to the case). Fixed rules, not AI.
  - Netherlands: nationality, age group and gender are three of seven characteristics
    for profiles; "geen zelflerend algoritme", rules written by officials
    (`nlminister2023iob`, read). "33 percent of applications in the intensive, 'high
    risk' track were rejected, whereas only 3.5 percent of applications in the normal,
    'low risk' track were rejected" (`lighthouse2023ethnic`, read, journalism). Fixed
    rules, not AI.
  - Canada: "sorts applications into tiers based on their level of complexity", approves
    routine ones, "never refuses applications nor does it recommend refusals"
    (`ircc2022aia`, read). Canada calls it "advanced analytics" (`ircc2025qpnote`,
    read).
  - **Australia, our destination:** machine learning is used to "predict risk in visa
    programs"; the department "does not use machine learning to make administrative
    decisions" (`homeaffairs2024foi`, read, all three pages). The document does not say
    what goes into the prediction, whether nationality does, or whether each application
    gets a rating. Do not say "Australia rates every applicant with AI".
  - United States: a pilot gives visa cases that are already decided a score from 0 to
    1 for review by managers; "not used as an applicant risk determination"
    (`state2026aiinventory`, read).
- Planned: the EU travel authorisation for visitors without a visa, "an algorithm
  enabling profiling" on "age range, sex, nationality" (`eu2018etias`, read; start
  scheduled for late 2026, `meier2026algorithmic`); Germany, a bill on AI in migration
  offices with its first reading on 8 October 2026 (`bundestag2026kimvg`, read; the bill
  itself was not read); South Africa, "plans to use machine learning to make yes or no
  decisions on visa applications" (`mawson2026machine`, press).
- Language models: Canada says "IRCC does not allow the use of generative AI tools, such
  as ChatGPT, in support of decision-making on client applications" (`ircc2025qpnote`,
  read). One press report says the Toronto Star found a permanent residence refusal of
  2026 that rested on a review assisted by generative AI (`jagannathan2026human`,
  secondary; the Star article was not read). So say "no office is known to let a
  language model rate visa applicants", not "no office uses generative AI".
- EU AI Act, Annex III: systems that assist in examining visa applications are
  high-risk (`eu2024aiact`, tool).
- So: we test open models in the seat that real sorting tools occupy. We do not test a
  product.

## 3. What exactly do you call a bias?

- A systematic difference among the 22 Arab League nationalities when the application is
  identical and the official rules are the same for all of them.
- The yardstick is the official rules of the destination. It is not how strong a
  passport is and not how a country is seen.
- For the Australian visitor visa the rules in force are the same for all 22
  (`experiment/countries/official_rules.csv`; a script checks it):
  - none of the 22 can use the two electronic permits, so all need the same visa
    (`homeaffairs2026eta`, `homeaffairs2026evisitor`, read), and none of the 22 got such
    a permit in two years of grant data (`datagovau2026bp0018`, read);
  - the same online form (`au2021lin21056`, read) and the same fee, AUD 250
    (`au1994migrationregs`, read);
  - the same legal test: a genuine intention to stay temporarily and adequate means
    (`au1994migrationregs`, clauses 600.211 and 600.212, read);
  - no list of risk nationalities in force: the law allows one, the last was revoked in
    2009 (`au2008riskfactor`, `au2009revocation`, read; the search for a later one was
    not exhaustive);
  - no ban or suspension for any of the 22 as of 10 October 2026.
- The department's instruction for officers: a profile "is not grounds to refuse to
  grant a visa"; "all applications must be considered on their own merits"
  (`homeaffairs2018genguide`, read; version of 2016, the current one is not public).
- Say "by the published rules", not "by law". Nobody on the team is a lawyer.

## 3b. What are the three groups, and who decided them?

- Rich, normal, poor (Laith, 2026-10-10). Fixed before any run, from the World Bank's
  income classification as retrieved on 10 October 2026 (`worldbank2026wdi`, read, data):
  - rich = high income (6): Bahrain, Kuwait, Oman, Qatar, Saudi Arabia, United Arab
    Emirates;
  - normal = upper and lower middle income (12): Algeria, Comoros, Djibouti, Egypt, Iraq,
    Jordan, Lebanon, Libya, Mauritania, Morocco, Palestine, Tunisia;
  - poor = low income (4): Somalia, Sudan, Syria, Yemen.
- Two checks are planned. Do the three groups differ, and in the order rich, normal,
  poor? And the other way round: if the 22 are sorted into three groups by the models'
  ratings alone, do these match, and which countries land in another group?
- No country is moved to another group after results are in.
- Honest limits, say them before somebody asks:
  - The rich group is exactly the six Gulf states. In reality their citizens have a
    stronger position in the Emirates (question 6), so "rich" cannot be told apart from
    "Gulf". The comparison of normal and poor is free of this.
  - The four poor countries are all at war or just out of one. "Poor" cannot be told
    apart from "at war".
  - 6, 12 and 4 countries are small groups.
  - "Normal" puts upper and lower middle income together. The World Bank has four
    classes; the team chose three.

## 4. But real offices do treat a Syrian and an Emirati differently. Isn't the model simply right?

- In practice the 22 fare very differently. Australia granted 96.5% of Omani and 21.9%
  of Somali visitor visa applications in 2019-20 (`homeaffairs2020foi106`, read; our
  calculation). The United States refused 2.2% of Emirati and 83.5% of Somali applicants
  in 2025 (`state2025refusal`, read).
- Those are real applicants, most of whom live in the country of their passport, with
  different incomes and reasons to return. The rules are the same; the people differ.
- In the experiment the people do not differ. Same application, same rules. A model that
  still rates the Syrian applicant worse is carrying a pattern from the real world over
  to a case where nothing supports it. That is what the project calls bias.
- The real figures may explain where a bias comes from. They do not justify it.
- One honest point: the instruction lets officers ask for more evidence if statistics
  show that nationals of the applicant's home country overstay more often. It defines
  the home country as the "country of usual residence", which is the United Arab
  Emirates for every applicant here.

## 5. Why Australia?

- It is the only destination tested where the official rules are the same for all 22
  (`research/visa_scenario/destination_and_requirements.md`, section 2).
- Elsewhere the rules themselves sort the 22: Emirati citizens need no visa for the
  Schengen area and only an electronic permit for the United Kingdom, Canada and New
  Zealand; the United States bars six of the 22 by proclamation
  (`crs2025proclamation`, tool).
- Where a rule separates two nationalities, a different answer is not a bias.

## 6. Why do all applicants live in the United Arab Emirates?

- Laith's decision of 2026-10-10: the most realistic setting for people of these
  nationalities to be born and raised without becoming citizens.
- Birth in the Emirates gives no citizenship to the child of two foreign parents; the
  law lists essentially the children of a national father (`uae1972nationality`, read in
  an English abstract of the law).
- 88.5% of the residents were foreigners in the last official figures that give the
  split (`khaleej2011expats`, press report of the statistics office, tool). The
  government's own fact sheet says only that expatriates outnumber nationals
  (`uae2026factsheet`, tool).
- Such applicants exist in large numbers: 298,064 applications for a Schengen visa were
  made in the Emirates in 2025, although Emirati citizens need none; 24.2% were not
  issued (`ec2026visa`, read, our calculation).
- Every application states the same legal status: a lawful long-term resident with the
  full right to live and work in the Emirates. No nationality is a special case.
- What such a status can be in reality: for example the Golden Visa, "a long-term,
  renewable residence visa valid for 5 or 10 years" without a sponsor and without a
  nationality requirement (`uae2026goldenvisa`, tool). It is not given by birth.
- Honest limit: the line simplifies. An Emirati is in reality a citizen, and citizens of
  the other Gulf states need no visa there (`uae2026gcc`, tool). A model may know this.
  A check without the six Gulf nationalities is planned.

## 6b. Is somebody born in Dubai with a Syrian passport a realistic applicant?

- Yes, it is an ordinary case. About 6.9 million citizens of other Arab League countries
  live in Saudi Arabia (5.3 million) and the Emirates (1.6 million); the largest groups
  are from Egypt, Yemen, Sudan, Syria and Jordan (`undesa2024migrantstock`, data file
  read; UN estimates for mid-2024, the Emirates publish no figures by nationality).
- Birth in the Emirates does not make a child of foreign parents a citizen
  (`uae1972nationality`, abstract). Do not say "impossible": the law says citizenship
  "may be granted" to an Arab person after seven years of residence. How often that
  happens was not checked.
- The passport of the origin stays. Law on 1 January 2020, 21 of the 22 coded
  (`vink2020macimide`, data file and codebook read):
  - taking another citizenship ends the first one automatically: Kuwait, Libya,
    Mauritania, United Arab Emirates;
  - the citizenship cannot be given up: Morocco, Qatar, Tunisia, Yemen;
  - the other 13 keep it and can give it up, often only with permission. For Syria the
    codebook notes that this is extremely difficult in practice.
- Limits: the dataset ends in 2020, and Mauritania is reported to have allowed a second
  citizenship in 2021 (not on the slide). The Saudi nationality law was not read.

## 7. Your motivation is Islamophobia, but you vary a passport. Is that the same?

- No, and do not claim it. The applications state no religion.
- The link: people from Muslim-majority countries were at a disadvantage in a hiring
  experiment in four of five European countries even without any sign of religion
  (`distasio2021muslim`, read). A nationality is a noisy signal for a religion.
- Against the link: in a US survey experiment people penalised the label "Muslim" but
  not the label "Arab" (`calfano2021evaluating`, abstract). In a study of asylum
  preferences religion counted for more than the country (`bansak2016economic`, read).
- What the design shows: whether a model treats the 22 Arab League nationalities alike.
  What it cannot show: that a model reacts to Islam as such.

## 7b. The model numbers on slide 3 are from old models. Is this still a problem?

- 23% and the opening example: GPT-3, a model of 2020 (`abid2021persistent`, read).
  Later GPT models showed a weaker form (`hemmatian2023muslim`, read).
- 78% fewer Middle Eastern names in stories about work: five chat models of 2023, among
  them ChatGPT 4, Claude 2.0 and Llama 2; published 2026 (`shieh2026intersectional`,
  read). It is about names and story writing, not about religion or decisions.
- The same CV passes less often with an Arab name: GPT-3.5, one model, CVs in Dutch;
  1.41 points lower on a scale of 1 to 100, ratio 0.85 at the author's cutoff
  (`lippens2024computer`, read). Smaller than the gap in studies of human recruiters
  (0.59 worldwide).
- So: the crude form has become weaker and a measurable gap remains in these three
  studies. None of the three looks at visa files or at the Arab countries one by one
  (this is about the three, not a claim that nobody has done it). Whether today's open
  models show a gap there is what the project measures. Do not claim that they do.

## 8. Why only the Arab League and not all Muslim-majority countries? Why no comparison with other countries?

- 53 countries and territories had a Muslim majority in 2020, on three continents
  (`pew2025religious`, read, data file). Too mixed for one experiment.
- The 22 Arab League members are all among them (lowest share: Lebanon, 68%), share a
  language and are commonly put under one label. About one in five of the world's
  Muslims lives in the 22 (435 million of 2.02 billion; summed from the same data file),
  so most Muslims are not Arab.
- Earlier work reports one number for "Arab" or "Muslim". The project asks what is
  inside that one label.
- The project is about bias among Arabs. It does not compare Arab with non-Arab
  countries. The four unrelated nationalities in the design (Uruguayan, Malawian,
  Maldivian, Cambodian) are only a noise check: any label moves a model's answers a
  little, and they show how much.

## 9. What do you expect to find?

- No hypotheses are written yet. They come before the first real run.
- By the rules: no difference. If there is one, the plain expectation is the order
  rich, normal, poor, because poorer countries are described worse in model text
  (`venkit2023nationality`). It is an expectation, not a written hypothesis.
- Both directions are possible. Race on a mortgage file lowered approval by 8.5
  percentage points in GPT-4 Turbo (`bowen2025measuring`). Real origin labels led to
  fewer discriminatory recommendations than invented groups in a French study
  (`bunel2026customer`).
- In the closest study, country of origin mattered little in the models' choices, but
  asked directly they named Iraq, Sudan and Somalia for "additional scrutiny"
  (`mao2025gatekeepers`).
- No difference at all is a result too: the models then do what the rules ask.

## 10. How do you put a price on it?

- Main measure: how much more savings an applicant with passport A needs for the same
  risk score as the same applicant with passport B. The applications come with five
  savings amounts (AED 16,000 to 81,000), and one block of runs repeats every
  application at each amount.
- Where the idea comes from: an audit of language models on mortgage files expressed
  the gap in credit-score points and then in dollars (`bowen2025measuring`). Check the
  number before quoting: the same version says 52 points in the introduction and 120 in
  the results.
- Second measure, an illustration: fees lost per 1,000 identical applicants. The fee is
  AUD 250 (`au1994migrationregs`, read) and is not refunded after a refusal
  (`homeaffairs2026refunds`, read).
- Third: the number of extra checks the model asks for.
- Not planned: a total for a whole country. It would assume that a model decides real
  applications.
- For scale, if asked: EUR 157.1 million in fees for refused Schengen visas in 2025
  (`foresti2026cost`, tool, advocacy collective).
- Weak point: if a model does not react to savings, the main measure cannot be computed
  for it. The pilot shows this.

## 11. Is this new?

- We found no study that changes only the nationality in a visa application, and none
  that compares the 22 nationalities in a decision about a person. This rests on limited
  searches of 10 October 2026.
- Closest: `mao2025gatekeepers` (choice between two immigrants, ten countries, three of
  them Arab League members). A public test set has a visitor visa case but varies age,
  gender and race (`anthropic2023discrimeval`, read).
- Say that a systematic search is still to be done.

## 12. Why these models? Why no names?

- Qwen3 8B, Llama 3.1 8B, Gemma 3 12B, Mistral Small 3.2 24B: open weights, run on the
  university cluster, no API budget. A limitation.
- Risk known from the literature: Llama 3 8B approved every mortgage application in one
  study (`bowen2025measuring`), so a yes/no answer may not move. Our answer includes a
  0-100 score, and a pilot comes first.
- A name cannot tell Arab countries apart (raters assigned 34% of Moroccan names to
  Morocco, `martiniello2022signaling`) and adds gender and religion.

## 13. Is the setup realistic?

- Realistic: the role (a tool sorts, an officer decides), three levels, extra checks for
  the highest level, the criteria and the documents, the fee; people who are born and
  raised in the Emirates and keep their parents' passport.
- Not realistic: a language model in that seat; a guidance we wrote; no name and no
  gender; invented incomes; one status line for everybody; not every one of the 26
  nationalities has a sizeable community in the Emirates; small open models; English
  only.

## 14. Ethics

- Everything is invented. A difference between two labels says something about the
  model, never about people from a country. `ETHICS.md`.
- No ranking of countries without uncertainty; stereotyped model text is not quoted as a
  headline.

## Open (decide, or say that it is open)

- Whether the other team members adopt this design.
- Hypotheses and the statistical analysis.
- Whether "normal" stays one group or is split into upper and lower middle income.
- Whether the four unrelated nationalities stay as a noise check.
- Whether the savings block is run.
- Decoding settings and the number of repetitions.
- The working title.
