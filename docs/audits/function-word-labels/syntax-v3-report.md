# Shorter formulas, unchanged recognition requirements

Portuguese and Spanish thought/speech formulas now display **think / say / know / hope + que**. The rule and examples still show the following statement. Clause typing and complete clause recognition remain intact; formulas are teaching cues, not executable matchers.

A separate v3 bridge adds narrowly licensed **de + infinitive** constructions. It requires a matching dependency attachment, an infinitive, an explicit governor licence and a contiguous action subtree. Unknown noun relations, finite complements, multiple occurrences and conflicting parses still abstain.

On the same 334-example development pool, this recovers two previously missed examples:

- Portuguese **impedir + de + fazer isso** — a governed verb frame.
- Portuguese **jeito + de + fazer isso** — a noun followed by the action it describes.

Both preserve the full action “fazer isso”, rather than colouring only “fazer”. Assistant review finds both natural and correctly translated. These are known development regression cases, not fresh validation or an accuracy estimate. Counts change from 104 to 106 candidates; the other 228 examples abstain.

The eight-example staging overlay remains unchanged. The two recoveries are diagnostic until incorporated in a separately reviewed batch. No generated candidate is automatically published. The next substantive work is expanding independent source/parser coverage, resolving split nos safely and validating example quality separately from syntactic fit.
