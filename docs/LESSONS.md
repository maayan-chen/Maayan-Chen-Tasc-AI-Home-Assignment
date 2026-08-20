# Lessons

System-critical gotchas worth remembering — not a changelog.

<!--
THE TEST FOR AN ENTRY
Would reading this six months from now have prevented the bug?
If no → it's a changelog entry. Delete it. Git history already has it.

WHAT EARNS A PLACE
- Something that passed every automated check and still didn't work
- A fix that looks like an improvement but is a silent regression
- A failure whose symptom pointed somewhere unrelated to its cause
- A trap that will re-set itself for the next person

ENTRY SHAPE
## <The lesson stated as a claim>
<What happened. Why the intuitive reading is wrong. What the real signal is.
What to do instead — and, if the wrong fix is tempting, why it's wrong.>
→ `path/to/file`

The most valuable entries carry a WARNING AGAINST THE OBVIOUS FIX. A lesson
that only says "X was broken, we fixed it" doesn't stop the next person from
un-fixing it.

Where a lesson is worth enforcing, pin it with a test and say so in the entry.
Prose degrades; a red test does not.
-->

## {{Lesson stated as a claim}}
{{What happened, why it was surprising, what the real signal was, and what to do
instead.}} → `{{path}}`
