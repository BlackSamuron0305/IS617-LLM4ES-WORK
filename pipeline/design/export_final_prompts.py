"""Write readable copies of the final prompts to experiment/prompts/final_prompts/.

For every variant listed in final_prompts/prompt_overview.csv this puts the pieces together the way
build_runs does (main prompt, guidance with the rule of the variant, the three task wordings) and writes
one text file: base_prompt.txt for base, prompt_variants/<name>.txt for the others. The application
stays a placeholder ({application}). The files are for reading only; the runs are still built from
main_prompts/, task_wordings/ and variants.csv, so after a change there, run this script again.

Usage:
    python -m pipeline.design.export_final_prompts
"""

from pipeline.core import common
from pipeline.core.common import EXPERIMENT
from pipeline.design.build_runs import BASE_VARIANT, POLICY_PLACEHOLDER, WORDINGS, build_policy, load_variants, read_text

FINAL = EXPERIMENT / "prompts" / "final_prompts"
LINE = "=" * 72


def assemble(variant):
    main = read_text(f"prompts/{variant['main_prompt']}")
    if variant["guidance"]:
        main = main.replace(POLICY_PLACEHOLDER, build_policy(variant["guidance"], variant["rule"] or None))
    parts = [f"VARIANT: {variant['variant']}",
             "Built from: " + "; ".join(x for x in (f"prompts/{variant['main_prompt']}", f"prompts/{variant['wordings']}/",
                                                      f"inputs/policy/{variant['guidance']}" if variant["guidance"] else "",
                                                      f"inputs/policy/{variant['rule']}.txt" if variant["rule"] else "") if x),
             "The application is inserted where {application} stands (pairwise: {application_a} and {application_b}).",
             "", LINE, "SYSTEM PROMPT", LINE, main.rstrip("\n")]
    for n in WORDINGS:
        parts += ["", LINE, f"USER MESSAGE, WORDING {n} OF 3", LINE, read_text(f"prompts/{variant['wordings']}/task_wording_{n}.txt").rstrip("\n")]
    return "\n".join(parts) + "\n"


def main():
    variants = load_variants()
    names = [row["name"] for row in common.read_table(FINAL / "prompt_overview.csv")]
    (FINAL / "prompt_variants").mkdir(parents=True, exist_ok=True)
    for name in names:
        path = FINAL / ("base_prompt.txt" if name == BASE_VARIANT else f"prompt_variants/{name}.txt")
        path.write_text(assemble(variants[name]), encoding="utf-8", newline="\n")
    print(f"wrote {len(names)} prompts to {FINAL}")


if __name__ == "__main__":
    main()
