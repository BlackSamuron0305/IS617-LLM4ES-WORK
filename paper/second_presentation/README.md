# Second presentation: midterm

**11-12.11.2026.** 10 minutes for each team + 5 minutes of Q&A. 10 points.

Criteria, copied from the course
[grading rubric](https://github.com/dess-mannheim/LLM4ESS/blob/main/grading_rubric.md)
(read 2026-10-04):

- [ ] Brief research question and motivation [1]
- [ ] Data and methods [5]
- [ ] Preliminary results [3]
- [ ] Planned next steps [1]

Not every member has to present, but all members should be prepared to answer questions.
Keep to the allocated time.

The slides (PowerPoint) go in this folder.

**`midterm.pptx`** was built by Claude Code on 2026-11-02 at Laith's explicit request, wording included
(`build_midterm.py` builds it from `results/audited_models/` and `figures/`; facts and sources are in the speaker notes). The team
rewrites the wording or declares the use of AI. Open `midterm.pptx` in PowerPoint to check the layout before presenting; the
numbers come from the tables of the main run and the judge, which is not validated yet.

**Design (2026-11-04, at Laith's request: "more similar to the first design").** The deck now uses the pitch
(`../first_presentation/pitch_v8.pptx`) as its template: the same theme (navy and gold, Cambria titles), the same layouts
with footer and slide number, the pitch's title slide with the 22 flags, its icons, cards, question line and source line.
Titles are 32 pt instead of the pitch's 36 because they are longer. The figures in `figures/` are drawn in the deck's colours
(`python -m pipeline.analysis.make_figures ... --style deck`, command in `build_midterm.py`); the paper keeps its own copies in
the default style. The wording on the slides and in the speaker notes is unchanged, except for a short source line under
most slides and number callouts beside the charts, all taken from the speaker notes and the result tables.

**Deep dive added (2026-11-05, at Laith's request).** Two slides after the outlier slide (slides 12 and 13: thinking and temperature; conflict
countries) and updated limits and next steps (slide 16). Figures: `python -m pipeline.deep_dive.make_thinking_figures --style deck --out paper/second_presentation/figures`.
Numbers come from `results/deep_dive/`; all of it is exploratory (`experiment/planning/deviations.md` D8). The deck now has 16 slides: check the time (10 minutes) and cut if needed.
