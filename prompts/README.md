# Prompt texts

| File | Used by |
|---|---|
| `lesson.txt` | the +lesson condition (appended to each update input) and the history + lesson / lesson-in-prompt references; identical for every chain and level |
| `lesson_convention.txt` | first three sentences of the lesson (history + convention, convention-only variants) |
| `lesson_procedure.txt` | the procedure part (history + procedure, procedure-only variants) |
| `gepa_note_neutral.txt` | GEPA format note of the main results (`CLRBENCH_GEPA_NOTE=neutral`) |
| `gepa_note_explicit.txt` | GEPA note that names the test aggregation (`CLRBENCH_GEPA_NOTE=explicit`) |
| `class_names/<chain>.txt` | class-name oracle: one line per label ("review queue B8 stands for: ...") |
| `web_lookup/<chain>.txt`, `<chain>.nogold.txt` | web-lookup references: named groupings that contain each label's example, with and without the hidden class |
| `update_guideline_hypothesize.txt` | generic "hypothesize a category before recording" update guideline (variant `hypm`) |

The task prompts of every level are in `data/chains/<chain>/prompts/` and inside the task files. Solver and update
prompts of the methods are built in code: `harness/runtime/*/solver.py` and `common.py` (solver), the method adapters
in `methods/`, and the official prompt files `methods/shared/dc_curator.txt`, `rb_memory_instruction.py` and
`tfgrpo_prompts.yaml`. Practice feedback (counterexample and the explicit membership sentences) is generated in
`harness/runtime/self/feedback_m4.py`.
