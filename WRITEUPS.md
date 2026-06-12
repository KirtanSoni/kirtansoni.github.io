# How to write a writeup

Derived from a close read of [eieio's "Scaling One Million Checkboxes"](https://eieio.games/blog/scaling-one-million-checkboxes/) — the benchmark for engineering writeups on this site. The core insight: **it's a story with technical payloads, not a feature list with adjectives.**

## The story-beat template

Every writeup follows an arc. Map your material onto it before writing a single sentence:

1. **Hook + stakes** (first 3-4 sentences) — what you built, the one number or fact that makes it interesting, and the gap between expectation and reality. eieio: *"I built the site in 2 days. I thought I'd get a few hundred users, max. That is not what happened."* Setup → subversion. Short declaratives.
2. **The promise** — one line telling the reader what journey they're on: *"Let's talk about how I kept the site (mostly) online!"* The "(mostly)" does double duty: honesty and voice.
3. **Just-enough context** — the architecture/starting point, explained only as deep as the story needs. Reasoning over inventory: not "the stack is X, Y, Z" but "I could have done this with a single process, but I wanted an excuse to use Redis."
4. **Escalation / first contact with reality** — the thing that broke, surprised, or grew. Time-anchor it. This is where diagrams and stats belong: at the moment the reader needs them to feel the problem.
5. **Crisis → decision → consequence** (repeat as needed) — each technical decision is a plot point with a before and after. What you believed, what happened, what you changed, what it cost.
6. **Resolution** — where it landed. Numbers again, now as payoff instead of stakes.
7. **Reflection** — what you actually learned, said plainly. Not a summary; a takeaway you didn't have at the start.

## Section titles are narrative beats

eieio's headings: *"Day 1: the pop"*, *"It was not a good night to have plans"*, *"Adding a replica and portscanning my VPC"*. Time-anchored, story-forward, slightly weird. Never "Architecture Overview", "Features", "Conclusion".

## Voice rules

- **First person, past tense, honest.** Mistakes are plot points, not embarrassments to hide: *"foolishly stored in Redis!"*, *"There's a race here. It bit me pretty early on."*
- **Short sentences carry the drama.** Long sentences carry the explanation. Alternate.
- **Numbers create stakes, not decoration.** "650,000,000 checks" in the title. "125KB of state" makes the architecture click. A number per beat; never a wall of them.
- **Explain reasoning, not inventory.** Every "what" gets a "because". If a paragraph could appear in the README, it doesn't belong in the writeup.
- **Code appears mid-story** with conversational comments ("It's pretty sweet."), trimmed to the part that matters, introduced by why you're showing it.
- **End sections with momentum** — a consequence or an open question that pulls into the next beat.

## What goes in sidenotes (`.sn`)

The margin is for the second voice — the author leaning over to whisper. Use it for:
- honest caveats (*"I later gave up on this approach"*)
- self-aware asides (*"I originally only kept the latest 1 million logs for a given day(!)"*)
- technical tangents that would derail the paragraph
- jokes that reward attentive readers

Never restate the main text. Never put load-bearing information in a note. Syntax: see "Sidenotes" in README.md.

## How the site components serve the story

- `.lede` — beats 1-2 compressed into two sentences.
- `.pipe` / `.flow` — at the *moment of explanation*, right where the reader needs the shape of the system. Never decorative.
- `.stats` — at moments of stakes (beat 4) or payoff (beat 6).
- `.decision` — beat 5's crisis→decision pairs, when the rationale deserves a box.
- `.term` / `.term-window` — show, don't describe: real output at the moment it happened.
- `.cardgrid` good/bad — before/after or with/without contrasts.
- `.colophon` — stack + layout footer; keeps inventory out of the prose.

## Sounding organic (the anti-slick rules)

The fastest way to sound machine-written is to make every paragraph land a zinger. Don't.

- **One earned aphorism per post, maximum.** If two paragraphs in a row end with a punchline, delete the weaker one and end that paragraph plainly.
- **Prefer plain causality over constructed antithesis.** "Without dedup the LLM stage would never keep up" beats "Dedup isn't a feature; it's a philosophy."
- **Let experience carry claims.** "It got things right often enough that I stopped checking" is more credible than a symmetrical maxim about small models.
- **Vary the rhythm irregularly.** Real writing has paragraphs that just end. Some sentences are merely functional. That's fine — that's what makes the good lines land.
- **Admit deliberation, not just conclusions.** "I considered building a web UI and decided against it" reads human; a verdict with no visible thinking reads generated.
- **Cut anything that sounds like it wants to be quoted.**

## Before / after

**Before (feature prose — what we're not doing):**
> Automata is a daily job-scraping pipeline with LLM evaluation. It features Playwright-based extractors for Microsoft, Nvidia and Apple, SQLite persistence with deduplication, structured extraction via LangGraph, and ntfy.sh notifications.

**After (story):**
> Checking three career sites every morning is a robot's job, so I built the robot. Every day at 9:00 it scrapes Microsoft, Nvidia, and Apple, asks a local LLM one question about each new posting — *how many years of experience does this actually require?* — and pings my phone only when the answer is one I'd want to hear. The interesting part was getting a GPU in my closet to answer that question reliably thousands of times.

## Revision checklist

- [ ] Could the first three sentences appear in a README? If yes, rewrite them.
- [ ] Does every section heading advance the story?
- [ ] Is there a number in the first paragraph? Is every number doing work?
- [ ] Does every technical explanation arrive exactly when the story needs it?
- [ ] Is at least one mistake/failure told straight?
- [ ] Do the sidenotes whisper, or do they repeat?
- [ ] Does the ending say something you didn't know at the start?
