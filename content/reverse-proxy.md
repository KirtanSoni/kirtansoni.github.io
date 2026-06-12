---
title: ServeMux never forgets — a 430-line reverse proxy you reconfigure by typing at it
date: 2026-06-11
reading_time: 4 min read
description: I wanted every side project behind one domain without ever editing a config file, so I wrote a Go reverse proxy whose route table is edited from the server's own stdin. Go's ServeMux refused to forget a route, and autocert made my best-tested package redundant.
tags: [Go, Networking, TLS, Infrastructure]
---

<p class="lede">I wanted every side project reachable under one domain without ever editing a config file again. So I wrote a ~430-line Go reverse proxy whose route table you edit by typing commands into the running server's stdin. Two things happened on the way: Go's <code>ServeMux</code> refused to forget a route, and six lines of <code>autocert</code> made my most thoroughly tested package obsolete.</p>

<h2>Heavier than the problem deserved</h2>

<p>
The goal was simple: every project lives at <code>https://&lt;domain&gt;/projects/&lt;path&gt;</code>, and adding a new one shouldn't mean redeploying anything. nginx does this, obviously.<span class="sn"><label class="sn-pill" for="reve-nginx"></label><input class="sn-toggle" type="checkbox" id="reve-nginx"><span class="sn-note">nginx reloads its config with one command, in under a second, without dropping a connection. The heaviness I was avoiding was mostly in my head. Building it anyway was the point.</span></span> But editing a config file and reloading felt heavier than the problem deserved, and I wanted to know what <code>net/http/httputil</code> actually gives you for free. The bet: one Go binary, a <code>httputil.ReverseProxy</code> per upstream, and a route table you can rewrite while the server is serving.<span class="sn"><label class="sn-pill" for="reve-commits"></label><input class="sn-toggle" type="checkbox" id="reve-commits"><span class="sn-note">The repo's entire git history is two commits, three minutes apart: "Initial commit" and "final push". All of the actual work happened off the record in between.</span></span>
</p>

<div class="pipe">
  <span class="box">client</span><span class="arr">→</span>
  <span class="box">:443 TLS (autocert)</span><span class="arr">→</span>
  <span class="box">security headers</span><span class="arr">→</span>
  <span class="box">/projects/* → route lookup</span><span class="arr">→</span>
  <span class="box">ReverseProxy</span><span class="arr">→</span>
  <span class="box">upstream</span>
</div>

<p>
Port 80 exists only to answer ACME HTTP-01 challenges and redirect everything else to HTTPS. The real handler chain lives on 443. That part went exactly as planned. The route table did not.
</p>

<h2>ServeMux never forgets</h2>

<p>
The core is <code>RuntimeMux</code>: an <code>RWMutex</code>-guarded map of path → <code>Service</code> (name, path, target URL, and a live <code>httputil.NewSingleHostReverseProxy</code>), wrapped around a standard <code>http.ServeMux</code>. Add a route, register the pattern, done. Then I went to write <code>remove</code> and hit the wall immediately: <b>Go's <code>ServeMux</code> has no unregister.</b> Once you <code>HandleFunc</code> a pattern, it's there for the life of the mux. The standard library hands you a registry and quietly omits the eraser.
</p>

<div class="decision">
  <b>Decision — resolve the route at request time, not registration time.</b> The handler
  registered on the mux is a closure that looks the path up in the live map on every request.
  Add = write to the map (and register the pattern only if it's new). Remove = nil the map entry.
  Re-adding the same path just swaps the map value, which means you can also <i>update</i> a
  service's upstream URL live — there's a test that flips a path between two backends and checks
  the second one answers. The pattern itself never leaves the <code>ServeMux</code>; the closure
  decides what happens.
</div>

<p>
One level of indirection, and the immutable registry stops mattering. The map is the truth; the mux is just a doorway.
</p>

<h2>Four commands, typed at a live server</h2>

<p>
With the table mutable, the management interface could be almost nothing: an interactive CLI reading the server's own stdin, running in a goroutine next to the listeners. Four commands, zero cleverness:
</p>

<div class="term-window">
  <div class="term-bar"><span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span><span class="term-title">proxy-server -domain example.com</span></div>
  <div class="term">
<span class="m">Proxy Management CLI</span><br>
<span class="m">Available commands: add, remove, list, exit</span><br>
<span class="b">&gt;</span> add API /api https://api-backend.example.com<br>
<span class="g">Added service API at path /api</span><br>
<span class="b">&gt;</span> list<br>
<span class="m">===== Services of RunTime Mux ========</span><br>
{"name":"API","path":"/api","url":"https://api-backend.example.com"}<br>
<span class="m">======================================</span><br>
<span class="b">&gt;</span> remove /api<br>
<span class="y">Removed service at path /api</span>
  </div>
</div>

<p>
A route added at <code>/api</code> is served at <code>https://&lt;domain&gt;/projects/api</code> — <code>http.StripPrefix("/projects", ...)</code> sits in front of the runtime mux, so upstreams never learn the prefix exists. That was the whole feature I'd set out to build, working. Routing turned out to be the easy half. Then I had to put HTTPS in front of it.
</p>

<h2>The 397 lines autocert made redundant</h2>

<p>
I did TLS the hard way first, on purpose. An <code>ssl</code> package: load a cert/key pair from disk, serve it by SNI through <code>tls.Config.GetCertificate</code>, pinned TLS 1.2+ cipher suites, tests for all of it.<span class="sn"><label class="sn-pill" for="reve-tests"></label><input class="sn-toggle" type="checkbox" id="reve-tests"><span class="sn-note">For the record: <code>proxy/</code>, the package that runs in production, has 187 lines of tests. <code>ssl/</code>, the package that doesn't, has 311. I tested the corpse more thoroughly than the patient.</span></span> It worked. Then I read what <code>golang.org/x/crypto/acme/autocert</code> actually does.
</p>

<div class="decision">
  <b>Decision — autocert instead of my own cert manager.</b> Issuance, renewal, HTTP-01
  challenge handling, and a disk cache — in about six lines of setup. The
  <code>autocert.Manager</code> hangs its challenge handler on port 80 and its
  <code>TLSConfig()</code> on the 443 server, and certificates just exist. My hand-rolled
  package is still in the repo, fully tested and entirely unused. That's the honest cost of
  learning by building: sometimes the lesson is "delete this." I haven't even managed the
  delete part.
</div>

<p>
The rest of <code>main.go</code> is plumbing done the boring, correct way, because a proxy is the one process that's never allowed to be the weak link: a middleware stamps every HTTPS response with the usual security headers (<code>Strict-Transport-Security</code>, <code>Content-Security-Policy</code> with <code>default-src 'self'</code>, <code>X-Frame-Options: DENY</code>, <code>X-Content-Type-Options: nosniff</code>, <code>Referrer-Policy</code>, <code>X-XSS-Protection</code>); both servers get read/write/idle timeouts and a max-header-bytes cap from flags; and SIGINT/SIGTERM trigger <code>http.Server.Shutdown</code> on both with a configurable deadline. The <code>proxy</code> package has tests for routing, fallback, live URL swaps, and concurrent add/remove under <code>-race</code>.
</p>

<h2>Six unchecked checkboxes</h2>

<p>
There's a requirements file in the repo — config-file routes, OAuth on certain paths, logging via Loki and Grafana, host-based rerouting, caching, a portfolio site. Every box is still unchecked, and the gaps are real. <b>Routes don't persist:</b> the initial <code>/wordsweave</code> route and the ACME contact email are hardcoded in <code>main.go</code>, and anything added through the CLI dies with the process. <b><code>remove</code> doesn't really 404:</b> because the <code>ServeMux</code> pattern can't be unregistered, removed paths fall through to a plaintext "Path not found" fallback that returns 200 — a wrong status code that happens to look fine in a browser. <b>The <code>ssl</code> package is dead code</b>, kept around as a candidate for a non-ACME deployment mode the running server has never needed. And the root handler at <code>/</code> is a stub for the portfolio site that doesn't exist yet.<span class="sn"><label class="sn-pill" for="reve-hello"></label><input class="sn-toggle" type="checkbox" id="reve-hello"><span class="sn-note">Specifically, it returns the five bytes <code>hello</code>. The portfolio has been "next up" since March 2025.</span></span> Next, in order: config-file-driven routes so the CLI edits something durable, a real 404 on remove, then logging.
</p>

<p>
I went in to learn what <code>httputil</code> gives you for free, and it does give you a lot — the actual proxying is a one-liner per upstream. The surprise was that the missing pieces were more instructive than the free ones. <code>ServeMux</code> not having an unregister forced the request-time-lookup design, which ended up being the best thing in the codebase — it's what makes live URL swaps possible at all. And <code>autocert</code> went the other way: 397 of my most carefully tested lines, made redundant by six. Build it yourself first; just be ready for the standard library to win.
</p>

<div class="colophon">
  <b>Stack:</b> Go 1.23 · <code>net/http</code> · <code>net/http/httputil</code> ·
  <code>golang.org/x/crypto/acme/autocert</code>.<br>
  <b>Layout:</b>
  <code>main.go</code> (servers, autocert, headers, shutdown) ·
  <code>proxy/</code> (RuntimeMux + CLI, tested) ·
  <code>ssl/</code> (the cert manager autocert made redundant).
</div>
