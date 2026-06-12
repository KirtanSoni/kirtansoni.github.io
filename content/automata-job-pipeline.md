---
title: A GPU in my closet reads job postings now
date: 2026-06-08
reading_time: 5 min read
description: Automata — a daily pipeline that scrapes Microsoft, Nvidia, and Apple postings, asks a local 3B model one question about each, and only pings my phone when the answer is good.
tags: [Python, LLM, vLLM, Pipelines, Automation]
---

<p class="lede">I was checking the same three career pages every morning, so I automated myself out of the loop. Every day at 9:00 a pipeline scrapes Microsoft, Nvidia, and Apple, asks a small local LLM one question about each new posting — <i>how many years of experience does this actually require?</i> — and pings my phone only when the answer is one I'd want to hear.</p>

<p>
The first 24 hours of scraping pulled <b>2,688 postings</b>: 1,593 from Apple, 925 from Nvidia,
and 170 from Microsoft.<span class="sn"><label class="sn-pill" for="sn-ms"></label><input class="sn-toggle" type="checkbox" id="sn-ms"><span class="sn-note">Not because Microsoft posts less — my extractor only asks for IC2/IC3 software roles there. Scoping the query is itself a filter.</span></span> Nobody is reading 2,688 job postings. And the one thing
I actually need to know — <i>is this role for someone at my level?</i> — is buried somewhere
around paragraph four, phrased a little differently every time.
</p>

<p>
Keyword filters can't read paragraph four. A language model can. What I didn't know was whether
a model small enough to run on a spare GPU could do it reliably, a thousand times a day,
without me babysitting it.
</p>

<h2>The shape of the thing</h2>

<div class="pipe">
  <span class="box">scrape</span><span class="arr">→</span>
  <span class="box">persist</span><span class="arr">→</span>
  <span class="box">details</span><span class="arr">→</span>
  <span class="box">LLM eval</span><span class="arr">→</span>
  <span class="box">categorize</span><span class="arr">→</span>
  <span class="box">notify</span>
</div>

<p>
Each stage only sees what the previous one lets through. The persist stage writes every scraped
posting into SQLite with <code>INSERT OR IGNORE</code> — the job ID and company form the primary
key — and emits <b>only the rows that were actually new</b>. On a normal morning that collapses
2,000+ scraped postings down to a few dozen. Without that step, every stage downstream would
re-read the entire job board every single day, and the LLM stage would never keep up.
</p>

<p>
New jobs get their full descriptions fetched (parallel Playwright browsers — the listing pages
give you titles and URLs, never the actual requirements), and then comes the interesting stage.
</p>

<h2>Asking 1,095 times</h2>

<p>
Evaluation runs against <b>vLLM serving Qwen2.5-3B</b> on a home GPU box.<span class="sn"><label class="sn-pill" for="sn-qwen"></label><input class="sn-toggle" type="checkbox" id="sn-qwen"><span class="sn-note">A 3-billion-parameter model is laughably small by 2026 standards. It is also free, private, 30&nbsp;seconds-per-request fast on local hardware, and entirely sufficient to find a number in a paragraph.</span></span>
The extraction is a LangGraph graph with structured output and a retry loop: the model must
return a typed record — <code>experience_years</code>, <code>visa_sponsorship</code>,
<code>clearance_required</code>, minimum and preferred qualifications — or it gets asked again.
Left to answer free-form, a model this size wanders. Pinned to a schema, with a validator
kicking malformed answers back for another try, it gets things right often enough that I
stopped spot-checking its work after the first few days.
</p>

<p>So far it has read 1,095 postings. Here's what paragraph four actually says:</p>

<div class="stats">
  <div class="stat">
    <div class="stat-num">2,688</div>
    <div class="stat-label">postings scraped in the first 24h</div>
  </div>
  <div class="stat">
    <div class="stat-num">1,095</div>
    <div class="stat-label">evaluated by the LLM</div>
  </div>
  <div class="stat">
    <div class="stat-num">150</div>
    <div class="stat-label">explicitly ask for ≤2 years</div>
  </div>
</div>

<p>
The distribution is bimodal in a way I didn't expect: big spikes at 5 years (249 postings) and
8 years (205), a long tail out to 20. Early-career roles are <b>14%</b> of what these three
companies post. 73 postings require a security clearance. And the bleakest number in the
database: the count of postings that explicitly promise visa sponsorship is
<b>zero</b>.<span class="sn"><label class="sn-pill" for="sn-visa"></label><input class="sn-toggle" type="checkbox" id="sn-visa"><span class="sn-note">Postings only ever volunteer the bad news — <code>visa_sponsorship</code> comes back "no" or "unknown", never "yes". The filter drops explicit "no"s and gives "unknown" the benefit of the doubt.</span></span>
</p>

<h2>Only good news reaches my phone</h2>

<p>
The categorize stage applies the policy: pass if the extracted requirement is
<b>≤ 2 years</b> — or if the model couldn't find one, because a posting that doesn't state a
requirement shouldn't be dropped by my robot's pessimism — and drop anything that explicitly
refuses visa sponsorship. Survivors go to <a href="https://ntfy.sh">ntfy.sh</a>, which pushes
them to my phone. There's a catch-up pass too: a job whose evaluation wasn't ready on the
morning it appeared gets alerted the next day instead of falling through a crack between
stages.
</p>

<div class="decision">
  <b>Decision — no dashboard.</b> The whole thing runs from a launchd plist at 09:00 daily and
  the only interface is the notification. I considered building a little web UI and decided
  against it: if I have to remember to go look at a tool, I've just rebuilt the thing I was
  trying to stop doing.
</div>

<h2>What I actually learned</h2>

<p>
Strip everything away and the useful output of this system is <b>one extracted integer per
posting</b>. The stage architecture, the dedup, the parallel browsers, the retry graph — all of
it exists so that one integer shows up reliably, every day, without me touching anything. I
went in expecting the LLM part to be the hard part. It wasn't. A small model with a rigid
schema and retries has been more dependable than any clever prompt I've written against a much
bigger model — the actual work was the plumbing around it.
</p>

<div class="colophon">
  <b>Stack:</b> Python · Playwright · SQLite · LangGraph · vLLM (Qwen2.5-3B-Instruct) ·
  ntfy.sh · launchd.<br>
  <b>Layout:</b> <code>run.py</code> (stage wiring) · <code>pipeline.py</code> (executor) ·
  <code>extractors/</code> (one per company) · <code>stages/</code> (persist → details → eval →
  categorize → notify) · <code>eval_graph.py</code> (structured extraction + retry) ·
  <code>launchd/</code> (the 9:00 schedule).
</div>
