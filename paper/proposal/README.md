# Proposal

`proposal.tex` / `proposal.pdf`: the project plan to send to the professor for feedback
before the pitch (13.10.2026). Three pages of text plus references in the
[ACL template](https://github.com/acl-org/acl-style-files), the same format as the final
paper. `acl.sty` and `acl_natbib.bst` must stay next to `proposal.tex`. The bibliography
is `../final_paper/custom.bib`.

- **This is the proposal for the bank design, written on 2026-10-08.** The proposal for
  the hiring design (2026-10-04) is in `research/old_design/hiring_2026-10-04/proposal/`.
  If the earlier one was already sent to the professor, say in the covering e-mail that
  the topic changed and why.
- **First draft written by Claude Code at Laith's request.** Read it, correct it and put
  it into your own words before sending. It ends with an "AI use" line that says so.
- Every source cited was read at full-text level or in the cited sections
  (`research/literature_matrix.csv`). Laws and guidelines were read in single sections
  only. Two sources are company websites and one is a press report; the text says so.
- The sentence that no such study was found rests on a few web searches, not on a
  systematic search. The proposal says so.
- The course repository (read 2026-10-04) lists no proposal and no criteria for one. It
  is not a graded deliverable.

Build: `latexmk -pdf proposal.tex`, then `latexmk -c proposal.tex` to remove build files.
The template needs the LaTeX packages `caption`, `enumitem` and `upquote`. On Laith's
TinyTeX they were missing on 2026-10-08 (`tlmgr update --self`, then
`tlmgr install caption enumitem upquote`).
