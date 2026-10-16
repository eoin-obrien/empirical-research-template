---
name: academic-writing
description: House rules for drafting or revising academic prose — manuscript sections in paper/, research documents in docs/, abstracts, responses to reviewers. Use when writing or editing research text, not code, READMEs or chat replies.
---

# Academic writing

Apply these rules to the text you were asked to write or revise. Do not
rewrite surrounding text; point out problems in it instead.

## Rules

**Claims.** State each claim at the strength its evidence supports. Name the
quantity, the population and the conditions. Prefer "reduced error by
{{< meta ... >}} on X" to "substantially improved performance".

**Evidence, inference, speculation.** Keep them distinguishable.

- Evidence: what was observed. Results sections report it.
- Inference: what follows from it, and why.
- Speculation: labelled as such ("one possible explanation is") and kept to
  the discussion.

**Causal language.** Use causal verbs (causes, leads to, improves, the effect
of) only when the design identifies the effect, through randomisation or a
stated identification strategy. Otherwise write "is associated with",
"predicts" or "co-occurs with".

**Citations.** Cite only keys that exist in `paper/references.bib`. Never
invent a reference, DOI, page number, quotation or author. If a claim needs a
source that is not in the bibliography, write `[CITATION NEEDED: <what>]` and
tell the user.

**Numbers.** Cite generated values with the `meta` shortcode, as described in
`docs/workflow.qmd`. Do not type results by hand.

**Restraint.** No generic significance claims ("has important implications",
"paves the way", "sheds light on"). If a result matters, state the specific
consequence. Hedge once, where the uncertainty is real; do not stack hedges
("may potentially suggest").

**No meta-commentary.** Do not narrate the text: "It is worth noting that",
"In this section, we discuss", "Importantly,". A short roadmap at the end of
the introduction is the exception.

**No stock transitions or vocabulary.** Avoid sentence-initial "Moreover",
"Furthermore", "Additionally", "Notably", "Overall". Show the logical relation
or use none. Avoid "crucial", "pivotal", "underscores", "delve", "showcase",
"landscape" (unless literal), "a testament to", and the "not X but Y"
construction used for emphasis.

**No repetitive conclusions.** Do not end paragraphs or sections by restating
them. The conclusion states each finding once.

**Vale is a prompt, not a target.** Treat Vale warnings as cues for judgment.
Do not distort a sentence only to silence a warning.

## End-of-pass audit

After writing or revising, check your own text and report the result to the
user in a few lines:

1. Every empirical claim traces to a result, a citation, or is labelled as
   inference or speculation.
2. Every citation key exists in `paper/references.bib`. Check with Grep.
3. Every causal verb is justified by the design.
4. Every result number is a generated value, not typed.
5. No meta-commentary, stock transitions or listed vocabulary remain.
6. No paragraph or section ends by restating itself.
7. No generic significance claim remains.

List any `[CITATION NEEDED]` placeholders and any item you could not satisfy.
Run `just prose` if the text is in `paper/` or `docs/`.
