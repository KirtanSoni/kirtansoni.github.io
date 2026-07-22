---
title: Meet Forge: context management for AI agent harnesses
date: 2026-06-01
reading_time: 5 min read
description: A git-like CLI that gives AI agents a senior engineer's memory of your codebase: automatically, incrementally, and always in sync.
tags: [Rust, Agents, Claude, Tooling]
---

<p class="lede">A git-like CLI that gives AI agents a senior engineer's memory of your codebase: automatically, incrementally, and always in sync. Forge is part of <b>anvil</b>, a Claude-Code-like agentic harness written in Rust. <span class="pill">built in rust</span></p>

<pre><code>$ forge init && forge update</code></pre>

<h2>The problem: agents read code, they don't understand it</h2>

<p>
When an AI agent edits a file, it sees structure: function signatures, types, control flow.
What it <b>doesn't</b> see is the reasoning behind it.<span class="sn"><label class="sn-pill" for="sn-claudemd"></label><input class="sn-toggle" type="checkbox" id="sn-claudemd"><span class="sn-note">Claude Code's CLAUDE.md does this at the project level. Forge does it per file. The difference matters once a project stops fitting in one note.</span></span> Why does this file exist?
What must never change? Where does new code belong?
</p>

<p>
Without that context, agents make plausible-but-wrong decisions. They duplicate logic that
already exists elsewhere. They violate invariants that aren't written down. They refactor
things that can't be refactored.
</p>

<div class="cardgrid">
  <div class="card">
    <div class="card-label bad">Without Forge</div>
    <p>Agent reads <code>parser.rs</code>, 400 lines of syn AST traversal.</p>
    <p>It doesn't know the 15-line collapse threshold is a deliberate policy decision.</p>
    <p>It doesn't know non-Rust parsers should be sibling files, not added here.</p>
    <p>It makes a plausible change. It breaks something subtle.</p>
  </div>
  <div class="card">
    <div class="card-label good">With Forge</div>
    <p>Before touching the file, the agent reads its context note.</p>
    <p><em>"COLLAPSE_THRESHOLD must remain a named constant; it's a tunable policy decision."</em></p>
    <p><em>"Non-Rust parsers belong in sibling files, not here."</em></p>
    <p>The agent acts with intent. The change is correct the first time.</p>
  </div>
</div>

<blockquote>
Think of forge as the notes a senior engineer leaves on their first day handing off a file: not documentation, not a spec, but the things you'd only learn after breaking something in production.
</blockquote>

<h2>Four commands. That's the whole workflow.</h2>

<div class="steps">
  <div class="step">
    <div class="step-num">01</div>
    <div class="step-body">
      <div class="step-title">Initialize tracking</div>
      <p class="step-desc">Forge walks your project respecting <code>.gitignore</code>, records the current git hash for every source file, and creates a <code>.anvil/manifest.toml</code>. No context is generated yet, just a baseline snapshot. Fast and free.</p>
      <span class="step-cmd">forge init</span>
    </div>
  </div>
  <div class="step">
    <div class="step-num">02</div>
    <div class="step-body">
      <div class="step-title">See what's stale</div>
      <p class="step-desc">Compare stored hashes against current git state. Every file gets a clear status: up to date, stale (hash changed), or missing context. Like <code>git status</code> but for your agent's understanding of the codebase.</p>
      <span class="step-cmd">forge status</span>
    </div>
  </div>
  <div class="step">
    <div class="step-num">03</div>
    <div class="step-body">
      <div class="step-title">Generate or patch context</div>
      <p class="step-desc">For new files: sends full source to Claude and generates a structured context note. For changed files: sends only the git diff and the existing note, and Claude patches just the affected sections. Up to four files run concurrently. Prints a token and cost breakdown when done.</p>
      <span class="step-cmd">forge update</span>
    </div>
  </div>
  <div class="step">
    <div class="step-num">04</div>
    <div class="step-body">
      <div class="step-title">Wire up your agent</div>
      <p class="step-desc">Installs a <code>PreToolUse</code> hook into Claude Code's <code>settings.json</code>. From that point on, every time Claude reads a file forge silently injects its context note as <code>additionalContext</code> (no prompt changes, no manual steps). The agent always understands why a file exists before it touches it.</p>
      <span class="step-cmd">forge for-agent claude</span>
    </div>
  </div>
</div>

<div class="term-window">
  <div class="term-bar"><span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span><span class="term-title">forge status</span></div>
  <div class="term">
<span class="g">  ok      </span> <span class="m">crates/anvil-core/src/tools/read_file.rs</span><br>
<span class="g">  ok      </span> <span class="m">crates/anvil-core/src/utils/parser.rs</span><br>
<span class="y">  stale   </span> <span class="m">crates/forge/src/commands/update.rs (e8f53f6 → cfbe244)</span><br>
<span class="g">  ok      </span> <span class="m">crates/forge/src/git.rs</span><br>
<span class="y">  stale   </span> <span class="m">crates/forge/src/store/manifest.rs (e8f53f6 → cfbe244)</span><br>
&nbsp;<br>
<span class="m">28 up to date, 2 stale</span>
  </div>
</div>

<div class="term-window">
  <div class="term-bar"><span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span><span class="term-title">forge update</span></div>
  <div class="term">
<span class="g">  updated </span><span class="m">crates/forge/src/commands/update.rs</span><br>
<span class="g">  updated </span><span class="m">crates/forge/src/store/manifest.rs</span><br>
&nbsp;<br>
<span class="a">Usage  2 files  claude-sonnet-4-6</span><br>
<span class="m">  input       12,450  $0.0374</span><br>
<span class="m">  output       8,230  $0.1235</span><br>
<span class="m">  ─────────────────────────</span><br>
<span class="m">  total              </span><span class="a">$0.1608</span>
  </div>
</div>

<h2>Context files: six sections, every file, injected automatically</h2>

<p>
Each context file lives in <code>.anvil/</code> mirroring your source tree.
The format is fixed so agents can query specific sections rather than parsing
free-form prose.
</p>

<div class="anatomy">
  <div class="anatomy-header">📄 .anvil/crates/anvil-core/src/utils/parser.md</div>
  <div class="anatomy-body">
    <div class="anatomy-sections">
      <div class="anatomy-section active">## purpose</div>
      <div class="anatomy-section">## intent</div>
      <div class="anatomy-section">## structure</div>
      <div class="anatomy-section">## constraints</div>
      <div class="anatomy-section">## add here</div>
      <div class="anatomy-section">## do not add here</div>
    </div>
    <div class="anatomy-content">
      <div class="sec-title">## purpose</div>
      <p>Parses Rust source files using <code>syn</code> and converts the AST into a structured <code>FileSpec</code> summary that an AI agent can reason about without reading every line.</p>
      <br>
      <div class="sec-title">## constraints (example)</div>
      <p>• Must not panic on any valid Rust source file: unrecognized items return <code>None</code>, never unwrap<br>• <code>COLLAPSE_THRESHOLD</code> must remain a named constant, not an inline literal; it is a tunable policy decision<br>• Output must be deterministic for a given input, no random ordering, no timestamps</p>
    </div>
  </div>
</div>

<p>
Every context file answers the same six questions. An agent reading
<code>parser.rs</code> for the first time gets all of this before writing a single line.
</p>

<h2>Incremental updates: diffs in, patches out</h2>

<p>
Forge doesn't regenerate a context file from scratch every time a file changes.
It sends Claude the <i>diff</i> alongside the existing note and asks it to
patch only the affected sections. This keeps updates focused and API costs minimal.
</p>

<div class="flow">
  <div class="flow-row">
    <span class="flow-label">first run</span>
    <span class="box">full source</span><span class="arr">→</span>
    <span class="box">Claude</span><span class="arr">→</span>
    <span class="box">context.md</span>
  </div>
  <div class="flow-row">
    <span class="flow-label">on change</span>
    <span class="box">git diff</span><span class="arr">+</span>
    <span class="box">context.md</span><span class="arr">→</span>
    <span class="box">Claude</span><span class="arr">→</span>
    <span class="box">patched</span>
  </div>
</div>

<p>
The hash stored in <code>manifest.toml</code> is the commit hash of the file
at the last successful update, not HEAD. So if you update a file across three commits
before running <code>forge update</code>, the diff covers all three at once.
</p>

<h2>The .anvil store: structured like your project, committed with your code</h2>

<p>
Context files live in <code>.anvil/</code>, mirroring the source tree one-to-one.
The manifest tracks the hash for every file. Both are committed to git, so context
evolves alongside code and diffs are meaningful.
</p>

<div class="term">
<span class="b">.anvil/</span><br>
&nbsp;&nbsp;<span class="y">manifest.toml</span><br>
&nbsp;&nbsp;<span class="b">crates/</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="b">anvil-core/src/</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="a">tools/read_file.md</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="a">utils/parser.md</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="a">utils/formatter.md</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="a">utils/query.md</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="b">forge/src/</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="a">commands/update.md</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="a">commands/init.md</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="a">git.md</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="a">store/manifest.md</span><br>
&nbsp;<br>
<span class="y">manifest.toml</span><br>
<span class="m">  ↳ "crates/forge/src/git.rs" = "cfbe244..."</span><br>
<span class="m">  ↳ "crates/anvil-core/src/utils/parser.rs" = "cfbe244..."</span>
</div>

<h2>By the numbers: forged on itself</h2>

<p>
The first thing we ran forge on was anvil, the project that built it.<span class="sn"><label class="sn-pill" for="sn-cost"></label><input class="sn-toggle" type="checkbox" id="sn-cost"><span class="sn-note">$1.97 for thirty files of handoff notes. The per-run cost breakdown exists because surprise API bills are how side projects die.</span></span>
Here's what that looked like.
</p>

<div class="stats">
  <div class="stat">
    <div class="stat-num">30</div>
    <div class="stat-label">files tracked on init</div>
  </div>
  <div class="stat">
    <div class="stat-num">6</div>
    <div class="stat-label">sections per context file</div>
  </div>
  <div class="stat">
    <div class="stat-num">0</div>
    <div class="stat-label">stale after update</div>
  </div>
</div>

<div class="term-window">
  <div class="term-bar"><span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span><span class="term-title">forging anvil</span></div>
  <div class="term">
<span class="m">$ </span>forge init<br>
<span class="g">Initialized forge — tracking 30 files</span><br>
&nbsp;<br>
<span class="m">$ </span>forge update<br>
<span class="g">  updated </span><span class="m">crates/anvil-core/src/tools/read_file.rs</span><br>
<span class="g">  updated </span><span class="m">crates/anvil-core/src/utils/parser.rs</span><br>
<span class="g">  updated </span><span class="m">crates/forge/src/commands/update.rs</span><br>
<span class="m">  ... 27 more</span><br>
&nbsp;<br>
<span class="a">Usage  30 files  claude-sonnet-4-6</span><br>
<span class="m">  input      187,320  $0.5620</span><br>
<span class="m">  output      94,150  $1.4123</span><br>
<span class="m">  ─────────────────────────</span><br>
<span class="m">  total              </span><span class="a">$1.9743</span><br>
&nbsp;<br>
<span class="m">$ </span>forge for-agent claude<br>
<span class="g">forge → claude</span><br>
<span class="m">  hook     .claude/hooks/forge-context.sh</span><br>
<span class="m">  settings .claude/settings.json</span><br>
&nbsp;<br>
<span class="m">$ </span>forge status<br>
<span class="m">30 up to date, 0 stale</span>
  </div>
</div>

<h2>Design: built like git, reliable like a tool should be</h2>

<div class="cardgrid">
  <div class="card">
    <div class="card-label good">Atomic writes</div>
    <p>Context files are written to a temp path and renamed into place. A crash mid-write never leaves a corrupt file.</p>
  </div>
  <div class="card">
    <div class="card-label good">Partial failure</div>
    <p>One file failing to update doesn't abort the rest. Errors are collected and reported at the end.</p>
  </div>
  <div class="card">
    <div class="card-label good">Gitignore-aware</div>
    <p>Uses the same engine as ripgrep to walk your project. If git ignores it, forge ignores it. Any language, any file type.</p>
  </div>
  <div class="card">
    <div class="card-label good">Idempotent init</div>
    <p><code>forge init</code> fails immediately if <code>.anvil/</code> already exists. No half-initialized state.</p>
  </div>
  <div class="card">
    <div class="card-label good">Bounded concurrency</div>
    <p>Updates run four files at a time via a semaphore. Fast enough to not block you, conservative enough to not flood the API.</p>
  </div>
  <div class="card">
    <div class="card-label good">Transparent cost</div>
    <p>Every <code>forge update</code> run prints a full token and cost breakdown (input, output, cache reads and writes) so you always know what you spent.</p>
  </div>
</div>

<div class="colophon">
  forge is part of <b>anvil</b>, a Claude Code-like agentic CLI harness written in Rust.<br>
  <b>Built with:</b> anthropic-sdk-rust · tokio · syn · ignore · clap
</div>
