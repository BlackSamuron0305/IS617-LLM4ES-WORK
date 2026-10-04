# Proposal

`proposal.tex` / `proposal.pdf`: the project plan to send to the professor for feedback
before the pitch (13.10.2026). Two pages in the
[ACL template](https://github.com/acl-org/acl-style-files), the same format as the final
paper. `acl.sty` and `acl_natbib.bst` must stay next to `proposal.tex`. The bibliography
is `../final_paper/custom.bib`.

- **First draft written by Claude Code on 2026-10-04 at Laith's request.** Read it,
  correct it and put it into your own words before sending. It ends with an "AI use"
  line that says so.
- Every source cited was read at full-text level (`research/literature_matrix.csv`).
- The course repository (read 2026-10-04) lists no proposal and no criteria for one. It
  is not a graded deliverable.

Build: `latexmk -pdf proposal.tex`, then `latexmk -c proposal.tex` to remove build files.
