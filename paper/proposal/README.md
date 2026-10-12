# Proposal

`proposal.tex` / `proposal.pdf`: the project plan to send to the professor for feedback
before the pitch (13.10.2026). Just under four pages of text plus references in
the [ACL template](https://github.com/acl-org/acl-style-files), the same format as the
final paper. `acl.sty` and `acl_natbib.bst` must stay next to `proposal.tex`. The
bibliography is `../final_paper/custom.bib`.

- **This is the proposal for the visa design, written on 2026-10-10.** The proposal for
  the bank design (2026-10-08) is in `research/old_design/bank_2026-10-08/proposal/`,
  the one for the hiring design (2026-10-04) in
  `research/old_design/hiring_2026-10-04/proposal/`. If an earlier one was already sent
  to the professor, say in the covering e-mail that the topic changed and why.
- **First draft written by Claude Code at Laith's request.** Read it, correct it and put
  it into your own words before sending. It ends with an "AI use" line that says so.
- **Extended on 2026-10-12 by Claude Code at Laith's request.** The paragraph on machines
  that sort visa applicants now quotes its sources word for word, and a second paragraph
  adds what is planned. New in it: Australia (machine learning to "predict risk in visa
  programs"), the EU travel authorisation, the German bill and Canada's sentence on
  generative AI. Every quote was compared with the original document or page that day.
  Two things the text is careful about and the team should keep: the Australian document
  does not say what goes into the prediction, and no authority was found that lets a
  language model rate applications.
- **Not every source was read in full.** The proposal cites 39 sources. 31 were read in
  the text or data file itself, at least in the passages used: the Australian
  regulations, instruction, lists and the release on AI use, the US refusal table, the
  UK inspection report, the Canadian impact assessment and briefing note, the Dutch
  minister's answer, the article of the EU travel authorisation law, the German paper
  and the Bundestag page, the Pew and World Bank data, the summary of the German
  monitoring report, and the papers in the literature matrix as `fulltext`. Lighthouse
  Reports (33% and 3.5%) and the UK Human Rights Blog were checked on the page itself
  on 2026-10-12; both stay secondary sources. Eight were read only as an abstract or
  through a summarising tool and have to be checked on the original before sending: the
  EU Agency for Fundamental Rights survey (47%, 39%, 68%), the summary of the US
  proclamation, the EU AI Act annex, Calfano et al. (2021), and the four sources on the
  United Arab Emirates (an abstract of the nationality law, two government web pages,
  and a newspaper report of official population figures from 2011).
  The level of each source is in `research/literature_matrix.csv`.
- Four decisions of Laith of 2026-10-10 shape the text: the project is about LLM bias
  among the 22 Arab League countries, measured against the official rules (no passport
  strength, no non-Arab comparison groups); the second question is whether the countries
  can be grouped into rich, normal and poor; the applicants live in the United Arab
  Emirates; and every application states the same legal status. The proposal asks the
  professor about the yardstick in question 3, the setting in question 4 and the three
  groups in question 5.
- The Australian grant rates by citizenship (96.5% and 21.9%) are our calculation from
  the department's counts for 2019-20.
- The sentence that no such study was found rests on limited searches, not on a
  systematic search. The proposal says so.
- The design it describes was drafted by Claude and has not been confirmed by the team
  (`experiment/README.md`, "Added by Claude").
- The course repository (read 2026-10-04) lists no proposal and no criteria for one. It
  is not a graded deliverable.

Build: `latexmk -pdf proposal.tex`, then `latexmk -c proposal.tex` to remove build files.
The template needs the LaTeX packages `caption`, `enumitem` and `upquote`.
