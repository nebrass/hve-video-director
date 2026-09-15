# Phase 0: Discovery (Design Thinking)

Apply design thinking before creating anything. Understand the user, their audience, and the desired outcome.

## Step 0.0: Interpret the video request

Read the **Video Request** section in `project-plan.md` using the encoding contract in
`templates/project-plan.md`. The original request is provenance; this phase owns the researched
interpretation in `context.md`. A legacy project may have no original request: use its existing
context or ask what is missing, without inventing an earlier instruction.

Extract the requested **subject, goal, form, scenario, required detail, expected result, and
constraints**. Distinguish **user-stated**, **proposed from evidence**, and **not specified**.
For "demo XYZ end to end, showing each granular option", retain XYZ as the subject and granular
scenario coverage as a requirement. Do not broaden it to a whole-product tour or compress it to
feature highlights. A short promo request remains a short promo, not an automatic tutorial.

If XYZ names several features or cannot be identified, ask a focused clarification before
inventing a scenario. Explicit prompt content makes the questions relevant, but does not replace
the required Creative Brief or phase confirmations. Record requested duration/theme/voice only
when stated; they are not confirmed choices merely because they appear in this interpretation.

## Step 0.1: Empathize — Understand the Audience

**Ask how to gather context for the requested subject:**

```json
{
  "questions": [{
    "question": "How should we research the requested subject?",
    "header": "Input",
    "options": [
      { "label": "Analyze the codebase", "description": "Inspect the requested feature or product in the source project." },
      { "label": "I'll describe it", "description": "Use your explanation; ask for missing behavior or scenario details." },
      { "label": "Both", "description": "Combine focused source research with your positioning input." }
    ],
    "multiSelect": false
  }]
}
```

**If "Analyze the codebase" or "Both":**

Restore the bound `SOURCE_DIR` per `SKILL.md` Invocation. All source searches, file reads, and
history commands are rooted there, **not in the video output directory**. Exclude the generated
output subtree. Locate the named feature's entry points, controls/options, behavior, dependencies,
and relevant documentation; use its paths to narrow history and code searches. Do not summarize
unrelated features just because they appear in recent commits.

These are orientation reads, not the scope of the investigation; run only the applicable ones:
```bash
git -C "$SOURCE_DIR" log --oneline -100
head -80 "$SOURCE_DIR/README.md"
head -30 "$SOURCE_DIR/package.json"
```

Read the feature's actual implementation and docs before asserting its available options or
results. A missing file or a directory without a recognizable codebase supplies no product facts:
explain the gap and use clarification or the description-based path instead.

**If "I'll describe it":**

Use the user's explanation as the feature evidence. A quick source-rooted surface scan may add
context, but never overrides that explanation or supplies creative-brief defaults. Ask for
missing controls, actions, or expected results; do not invent a product workflow.

**Then ask the unanswered empathy questions (one at a time).** Read explicit answers back for
correction instead of repeating generic questions; never infer an answer the user did not give:

1. **Who will watch this video?** — Role, seniority, technical level
2. **What do they care about?** — What problem keeps them up at night?
3. **What should they do after watching?** — Sign up? Download? Book demo? Be impressed?
4. **What's the emotional journey?** — Should they feel excited? Relieved? Curious? Confident?

## Step 0.2: Define — Frame the Core Message

Present findings as dynamic selectable options **within the requested scope**. If the user named
XYZ, the feature-selection question is about XYZ's operations/aspects, not permission to add
unrelated product features. Keep a whole-product selection only for a whole-product request:

```json
{
  "questions": [
    {
      "question": "What's the product?",
      "header": "Product",
      "options": [
        { "label": "<detected-name>", "description": "Product name detected from the supplied context." },
        { "label": "<alternative>", "description": "A second plausible product framing." }
      ],
      "multiSelect": false
    },
    {
      "question": "Target audience?",
      "header": "Audience",
      "options": [
        { "label": "<detected-role>", "description": "Primary audience inferred from product research." },
        { "label": "<alternative>", "description": "A second plausible audience." }
      ],
      "multiSelect": false
    },
    {
      "question": "Key problems to address?",
      "header": "Problems",
      "options": [
        { "label": "<pain-1>", "description": "First researched audience pain." },
        { "label": "<pain-2>", "description": "Second researched audience pain." },
        { "label": "<pain-3>", "description": "Third researched audience pain." }
      ],
      "multiSelect": true
    },
    {
      "question": "Features to showcase?",
      "header": "Features",
      "options": [
        { "label": "<feat-1>", "description": "First researched product capability." },
        { "label": "<feat-2>", "description": "Second researched product capability." },
        { "label": "<feat-3>", "description": "Third researched product capability." },
        { "label": "<feat-4>", "description": "Fourth researched product capability." }
      ],
      "multiSelect": true
    }
  ]
}
```

Then ask CTA:
```json
{
  "questions": [{
    "question": "What should the call-to-action be?",
    "header": "CTA",
    "options": [
      { "label": "Visit website", "description": "Drive to a URL" },
      { "label": "Sign up / Get started", "description": "Push toward registration" },
      { "label": "Book a demo", "description": "Sales-oriented" },
      { "label": "Download / Install", "description": "Drive installs" }
    ],
    "multiSelect": false
  }]
}
```

## Step 0.3: Ideate — Generate Video Concepts

Based on the defined context, propose **2-3 video concepts** with different angles that all honor
the requested subject and depth. If the request already specifies its scenario, refine that
scenario rather than requiring replacement concepts. The examples below are starting points,
not permission to turn a detailed XYZ request into a grand tour:

For **Promo mode** example concepts:
- **The Problem Solver** — Lead with pain, reveal solution dramatically
- **The Transformation** — Before/after, show the contrast
- **The Social Proof** — Stats and results first, then show how

For **Showcase mode** example concepts:
- **The Grand Tour** — Walk through the entire app, highlight design choices
- **The Hero Feature** — Deep dive into one killer feature
- **The Day-in-the-Life** — Show the workflow from a user's perspective

For **Tutorial mode** example concepts (cold-open on the payoff, then task-ordered steps):
- **The Quick Start** — Open on the finished result, then the shortest happy path to reproduce it
- **The Build-Along** — Step-by-step in task order; the viewer follows each chapter and builds it themselves
- **The Fix-It Walkthrough** — Start from a common problem/error state and resolve it one step at a time

Present as selectable options. User picks one or mixes elements.

## Step 0.4: Define the requested demonstration scenario

Apply this step when the request calls for a scenario, walkthrough, or end-to-end demonstration.
Do not add a scenario inventory to a short promo solely because the template has a section for one.

Ground a typical scenario in the selected evidence: its starting state and data, the ordered
actions/configuration, intermediate states, and the **observable final result**. Proposals must
be labeled; source code or a user explanation is not evidence that a capture has already occurred.

Use the **Demonstration Scenario** inventory in `templates/context.md`. Assign stable `R1`, `R2`,
... requirement IDs to the steps, controls/options, and results the video must cover. Record each
item's source basis, demonstrated action/value, prerequisite, and visible outcome. The final
result must have its own row. IDs are ordinary prose/table content, not new director keys.

For "each granular option", enumerate the scenario's actual controls and available choices,
including conditional controls reached by it. Show the intended coverage to the user. If covering
mutually exclusive branches or every possible value would materially change the scenario, ask
what coverage they mean; do not silently reduce "every option" to a highlight reel or promise an
unrequested combinatorial tour. Unknown behavior remains unresolved, never invented.

The existing discovery checkpoint approves the interpretation and this inventory. Record the
approved scenario/requirement IDs and explicit scope changes in `project-plan.md`'s Decision Log
after the user's answer. Until then it is a proposal, not an approved coverage contract.

## Output

Generate `context.md` from `templates/context.md` with the researched request interpretation and,
when applicable, the proposed scenario inventory. Omit unused scenario sections; preserve the
original request only in `project-plan.md`. Do not write a placeholder context during intake.

## Checkpoint

> "Here's the proposed video about your requested subject:
> [Summary of subject, audience, goal, depth, and expected result from context.md]
>
> [For a scenario request: show the starting state, ordered actions/options, requirement inventory,
> unresolved items, and final result. Ask the user to confirm or correct this scope.]
>
> Next, Phase 1 is where **you choose how the video looks and sounds**: duration, theme, aspect
> ratio, identity/design system, voice, transitions, and music strategy. I may recommend an option
> with a reason, but I will not infer or select any of those choices from this research.
>
> Ready to move to Phase 1: Storytelling?"
