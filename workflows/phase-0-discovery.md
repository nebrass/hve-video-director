# Phase 0: Discovery (Design Thinking)

Apply design thinking before creating anything. Understand the user, their audience, and the desired outcome.

## Step 0.1: Empathize — Understand the Audience

**Ask how to gather context:**

```json
{
  "questions": [{
    "question": "How should we understand what this video is about?",
    "header": "Input",
    "options": [
      { "label": "Analyze the codebase", "description": "Deep dive into commits, code, README — I'll extract the story" },
      { "label": "I'll describe it", "description": "You tell me about the product/feature, I'll generate options" },
      { "label": "Both", "description": "Analyze code + your positioning input" }
    ],
    "multiSelect": false
  }]
}
```

**If "Analyze the codebase" or "Both":**

Do a deep analysis:
```bash
git log --oneline -100
head -80 README.md 2>/dev/null
cat package.json 2>/dev/null | head -30
ls -la src/ app/ pages/ components/ 2>/dev/null | head -20
```

Read key files to understand: product name, tech stack, main features, recent changes.

**If "I'll describe it":**

Quick surface scan (research context only — never creative-brief defaults):
```bash
head -30 README.md 2>/dev/null
ls src/ app/ 2>/dev/null | head -10
```

**Then ask empathy questions (one at a time):**

1. **Who will watch this video?** — Role, seniority, technical level
2. **What do they care about?** — What problem keeps them up at night?
3. **What should they do after watching?** — Sign up? Download? Book demo? Be impressed?
4. **What's the emotional journey?** — Should they feel excited? Relieved? Curious? Confident?

## Step 0.2: Define — Frame the Core Message

Present findings as dynamic selectable options:

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

Based on the defined context, propose **2-3 video concepts** with different angles:

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

## Output

Generate `context.md` from `templates/context.md` with all gathered information.

## Checkpoint

> "Discovery complete. Here's what I understand about your product and audience:
> [Summary of context.md]
>
> Next, Phase 1 is where **you choose how the video looks and sounds**: duration, theme, aspect
> ratio, identity/design system, voice, transitions, and music strategy. I may recommend an option
> with a reason, but I will not infer or select any of those choices from this research.
>
> Ready to move to Phase 1: Storytelling?"
