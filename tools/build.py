#!/usr/bin/env python3
"""Generate the Reachmap site.

Plain static HTML is what GitHub Pages serves, and what this writes. The only
reason a generator exists is that six pages share one header, one footer and one
nav, and keeping those in sync by hand is how a site drifts. Run it after
editing any page body:

    python3 tools/build.py

The output is committed, so the site needs no build step to deploy.
"""

import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "v0.3"
GH = "https://github.com/reachmap/reachmap.dev"
GH_SITE = "https://github.com/reachmap/reachmap.dev-website"

# (slug, title, nav label) — order is the docs reading order and the prev/next chain.
DOCS = [
    ("index",      "Documentation",        "Overview"),
    ("quickstart", "Quickstart",           "Quickstart"),
    ("detectors",  "What Reachmap detects","Detectors"),
    ("cluster",    "Cluster mode",         "Cluster mode"),
    ("ci",         "Gating a pull request","CI & policy"),
    ("catalog",    "The endpoint catalog", "Catalog"),
]


# Inline so the toggle needs no network and no icon font. CSS decides which of
# the two is visible, so the button is correct before any script runs.
THEME_ICON = (
    '<svg class="moon" viewBox="0 0 16 16" fill="none" stroke="currentColor" '
    'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M13.5 9.6A5.8 5.8 0 0 1 6.4 2.5 5.8 5.8 0 1 0 13.5 9.6Z"/></svg>'
    '<svg class="sun" viewBox="0 0 16 16" fill="none" stroke="currentColor" '
    'stroke-width="1.4" stroke-linecap="round" aria-hidden="true">'
    '<circle cx="8" cy="8" r="3.1"/>'
    '<path d="M8 1v1.6M8 13.4V15M15 8h-1.6M2.6 8H1M12.9 3.1l-1.1 1.1M4.2 11.8l-1.1 1.1'
    'M12.9 12.9l-1.1-1.1M4.2 4.2 3.1 3.1"/></svg>'
)


def head(title, desc, rel, *, go_import=True, page_class=""):
    """rel is the path prefix back to the site root ('' or '../')."""
    tags = []
    if go_import:
        # Inert until reachmap.dev is registered and pointed at Pages, at which
        # point this is what makes `go install reachmap.dev/cmd/reachmap` resolve.
        tags.append(
            '<meta name="go-import" content="reachmap.dev git '
            'https://github.com/reachmap/reachmap.dev">'
        )
        tags.append(
            '<meta name="go-source" content="reachmap.dev '
            'https://github.com/reachmap/reachmap.dev '
            'https://github.com/reachmap/reachmap.dev/tree/main{/dir} '
            'https://github.com/reachmap/reachmap.dev/blob/main{/dir}/{file}#L{line}">'
        )
    extra = "\n  ".join(tags)
    return f"""<!doctype html>
<html lang="en"{page_class}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(desc)}">
  <meta property="og:type" content="website">
  {extra}
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='13' font-size='13'>&#127760;</text></svg>">
  <link rel="stylesheet" href="{rel}assets/style.css">
  <script src="{rel}assets/theme-boot.js"></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""


def header(rel, current):
    def link(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{rel}{href}"{cur}>{label}</a>'

    return f"""<header class="site-head">
  <div class="wrap">
    <a class="brand" href="{rel}index.html">
      <span class="mark">&#9679;</span> reachmap
      <span class="ver">{VERSION}</span>
    </a>
    <nav class="site-nav">
      {link("index.html", "Overview", "home")}
      {link("docs/index.html", "Documentation", "docs")}
      <a class="gh" href="{GH}">GitHub</a>
      <button class="theme-toggle" type="button" aria-label="Toggle theme">{THEME_ICON}</button>
    </nav>
  </div>
</header>
"""


def footer(rel):
    return f"""<footer class="site-foot">
  <div class="wrap">
    <span>Reachmap &mdash; Apache-2.0</span>
    <a href="{GH}">Source</a>
    <a href="{GH}/blob/main/docs/DESIGN.md">Design</a>
    <a href="{GH}/blob/main/CHANGELOG.md">Changelog</a>
    <span class="spacer">Built from the {VERSION} tree.</span>
  </div>
</footer>
<script src="{rel}assets/site.js"></script>
</body>
</html>
"""


def term(label, body, copy=True):
    btn = '<button class="copy" type="button">copy</button>' if copy else ""
    return f"""<div class="term">
  <div class="term-bar">
    <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    <span class="label">{html.escape(label)}</span>{btn}
  </div>
  <pre><code>{body}</code></pre>
</div>"""


def anchor_headings(body):
    """Give every h2/h3 an id and a permalink."""
    def slug(text):
        t = re.sub(r"<[^>]+>", "", text)
        t = html.unescape(t).lower()
        t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
        return t

    def repl(m):
        tag, text = m.group(1), m.group(2)
        s = slug(text)
        return (f'<{tag} id="{s}">{text}'
                f'<a class="anchor" href="#{s}" aria-label="Permalink">#</a></{tag}>')

    return re.sub(r"<(h[23])>(.*?)</\1>", repl, body, flags=re.S)


def docs_nav(rel, current):
    items = []
    for slug, title, label in DOCS:
        cur = ' aria-current="page"' if slug == current else ""
        items.append(f'<li><a href="{rel}docs/{slug}.html"{cur}>{html.escape(label)}</a></li>')
    return f"""<nav class="docs-nav" aria-label="Documentation">
  <div class="group">Documentation</div>
  <ul>
    {"".join(items)}
  </ul>
  <div class="group">Repository</div>
  <ul>
    <li><a href="{GH}/blob/main/README.md">README</a></li>
    <li><a href="{GH}/blob/main/docs/DESIGN.md">Design notes</a></li>
    <li><a href="{GH}/blob/main/docs/LANDSCAPE.md">Landscape survey</a></li>
    <li><a href="{GH}/blob/main/CHANGELOG.md">Changelog</a></li>
  </ul>
</nav>"""


def page_nav(slug):
    idx = [d[0] for d in DOCS].index(slug)
    prev_l = nxt_l = "<span></span>"
    if idx > 0:
        s, t, lbl = DOCS[idx - 1]
        prev_l = f'<a href="{s}.html">&larr; {html.escape(lbl)}</a>'
    if idx < len(DOCS) - 1:
        s, t, lbl = DOCS[idx + 1]
        nxt_l = f'<a href="{s}.html">{html.escape(lbl)} &rarr;</a>'
    return f'<div class="page-nav">{prev_l}{nxt_l}</div>'


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("wrote", path)


def doc_page(slug, title, lede, body, desc):
    rel = "../"
    return (
        head(f"{title} &middot; Reachmap".replace("&middot;", "·"), desc, rel)
        + header(rel, "docs")
        + '<main id="main" class="wrap docs">\n'
        + docs_nav(rel, slug)
        + '<article class="docs-body">\n'
        + f"<h1>{title}</h1>\n"
        + f'<p class="page-lede">{lede}</p>\n'
        + anchor_headings(body)
        + page_nav(slug)
        + "</article>\n</main>\n"
        + footer(rel)
    )


# ---------------------------------------------------------------------------
# Real CLI output. Captured from the v0.3 tree against the fixtures in
# testdata/fixtures/. Nothing here is illustrative — if it changes, re-capture
# it rather than editing by hand.
# ---------------------------------------------------------------------------

SCAN_OUTPUT = """$ reachmap scan ./manifests

[workload] platform/ingestor deployment
    -> [cloud]    aws sqs events-inbound  [https, likely, messaging]
       platform.yaml:104  spec.triggers[0].metadata.queueURL
    -> [cloud]    aws msk events  [kafka/9094, likely, messaging]
       platform.yaml:109  spec.triggers[1].metadata.bootstrapServers
    -> [cloud]    aws rds ingestor-db  [likely, database]
       platform.yaml:32  spec.template.spec.containers[app].env[DATABASE_URL].valueFrom.secretKeyRef
    -> [cloud]    gcp sql analytics-primary  [postgres, confirmed, database]
       platform.yaml:46  spec.template.spec.containers[cloud-sql-proxy].args[1]
    -> [cloud]    aws ebs ingestor-spool  [confirmed, storage]
       platform.yaml:62  spec.template.spec.volumes[0].persistentVolumeClaim.claimName
    -> [external] Stripe  [likely, allowed, payments, pci]
       platform.yaml:116  spec.hosts
    -> [external] HashiCorp Vault (vault.internal.acme.io)  [confirmed, secrets]
       platform.yaml:83  spec.provider.vault.server
    -> [identity] iam-role platform-ingestor  [confirmed, identity]
       platform.yaml:10  metadata.annotations[eks.amazonaws.com/role-arn]
    -> [opaque]   secret platform/ingestor-api-creds [in vault.internal.acme.io at platform/ingestor/stripe-token]  [possible]
       platform.yaml:37  spec.template.spec.containers[app].env[VAULT_TOKEN_PATH].valueFrom.secretKeyRef

1 files, 10 objects, 1 workloads, 12 dependencies
9 classified targets, 1 unclassified, 1 secret-borne, 0 suppressed"""

DIFF_OUTPUT = """$ reachmap diff base.json head.json -fail-on new-external

1 new dependency
  + shop/orders  ->  api.riskscore.io  [https, possible, unclassified]
      orders.yaml:37

1 policy trigger fired
  ! [new-external] shop/orders -> api.riskscore.io: new external API dependency

$ echo $?
3"""

POLICY_OUTPUT = """$ reachmap policy check graph.json

warn  compliance-scoped-dependency  platform/ingestor -> Stripe
      platform.yaml:116
      This dependency is in a regulated scope. Confirm it is in the audit
      boundary and that data handling has been reviewed.
info  secret-borne-dependency  secret platform/ingestor-api-creds (OpaqueSecretRef)
      platform.yaml:37
      Dependency exists but its endpoint lives in a Secret, so manifest
      analysis cannot see the target.
info  workload-identity-binding  platform-ingestor (Identity)
      platform.yaml:10
      Workload assumes a cloud identity. Confirm the role's policy is scoped
      to what this workload actually needs.

0 error, 1 warn, 2 info"""


def colorize(text):
    """Colour real CLI output. Applied to captured text, never hand-written, so
    the page cannot drift from what the tool actually prints."""
    out = []
    for line in html.escape(text).split("\n"):
        raw = line
        if raw.startswith("$ "):
            cmd, *rest = raw[2:].split(" ")
            parts = [f'<span class="t-prompt">$</span> <span class="t-cmd">{cmd}</span>']
            for tok in rest:
                cls = "t-flag" if tok.startswith("-") else "t-cmd"
                parts.append(f'<span class="{cls}">{tok}</span>')
            out.append(" ".join(parts))
            continue
        if raw.startswith("[workload]"):
            out.append(f'<span class="t-ident">[workload]</span>'
                       f'<span class="t-src">{raw[10:]}</span>')
            continue
        m = re.match(r"^(\s*)-&gt; (\[\w+\]\s*)(.*)$", raw)
        if m:
            indent, kind, rest = m.groups()
            k = kind.strip()
            cls = {"[cloud]": "t-cloud", "[external]": "t-ext", "[identity]": "t-ident",
                   "[opaque]": "t-opaque", "[service]": "t-cloud", "[store]": "t-cloud"}.get(k, "t-meta")
            rest = re.sub(r"\[([^\]]*)\]$",
                          lambda mm: '[' + ", ".join(
                              f'<span class="t-conf">{p}</span>' if p.strip() == "confirmed"
                              else f'<span class="t-likely">{p}</span>' if p.strip() == "likely"
                              else f'<span class="t-poss">{p}</span>' if p.strip() == "possible"
                              else f'<span class="t-meta">{p}</span>'
                              for p in mm.group(1).split(", ")) + ']',
                          rest)
            out.append(f'{indent}<span class="t-arrow">-&gt;</span> '
                       f'<span class="{cls}">{kind}</span>{rest}')
            continue
        if re.match(r"^\s{5,}\S+\.(yaml|yml|json):\d+", raw):
            out.append(f'<span class="t-meta">{raw}</span>')
            continue
        if raw.lstrip().startswith("+ "):
            out.append(f'<span class="t-add">{raw}</span>')
            continue
        if raw.lstrip().startswith("! ") or raw.startswith("warn "):
            out.append(f'<span class="t-warn">{raw}</span>')
            continue
        if raw.startswith("info "):
            out.append(f'<span class="t-meta">{raw}</span>')
            continue
        if re.match(r"^\d+ (files|new|policy|error)", raw) or re.match(r"^\d+ classified", raw):
            out.append(f'<span class="t-meta">{raw}</span>')
            continue
        if raw.startswith("      ") and raw.strip():
            out.append(f'<span class="t-meta">{raw}</span>')
            continue
        out.append(raw)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------

def landing():
    rel = ""
    return (
        head("Reachmap — map what your Kubernetes workloads reach",
             "A dependency mapper for distributed systems. Reads rendered Kubernetes "
             "manifests or a live cluster and catalogs every cloud service, internal "
             "service and third-party API a workload reaches — with the file and line "
             "behind every claim.", rel)
        + header(rel, "home")
        + f"""<main id="main">

<section class="hero">
  <div class="wrap">
    <h1>Map what your workloads<br><span class="dim">actually reach.</span></h1>
    <p class="lede">
      Reachmap reads rendered Kubernetes manifests &mdash; or a live cluster &mdash; and
      catalogs every <strong>cloud service</strong>, <strong>internal service</strong> and
      <strong>third-party API</strong> a workload depends on. Every edge carries the file,
      the line and the field it came from, because the first question anyone asks about a
      surprising dependency is <em>says who?</em>
    </p>
    <div class="cta-row">
      <a class="btn btn-primary" href="docs/quickstart.html">Quickstart &rarr;</a>
      <a class="btn" href="docs/detectors.html">What it detects</a>
      <a class="btn" href="{GH}">Source</a>
    </div>

    {term("reachmap scan", colorize(SCAN_OUTPUT))}

    <p class="sec-intro" style="margin-bottom:0">
      No agent, no cluster, no credentials. That scan is a directory of YAML and a
      single static binary.
    </p>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sec-label">The problem</div>
    <h2>A pod spec is not the dependency list</h2>
    <p class="sec-intro">
      Most of what a service reaches is written down somewhere other than its container
      environment &mdash; in an autoscaler, a sidecar argument, a Secret it mounts, or an
      annotation on its ServiceAccount. Four of Reachmap's detectors exist because those
      dependencies are otherwise invisible.
    </p>
    <div class="grid grid-2">
      <div class="cell">
        <span class="tag">keda-trigger</span>
        <h3>The queue nobody can see</h3>
        <p>A worker that only consumes from SQS has no inbound Service, no ingress and no
        endpoint in its own environment. The queue lives in the autoscaler's configuration.
        Without reading KEDA triggers, that workload looks like it depends on nothing.</p>
      </div>
      <div class="cell">
        <span class="tag">proxy-sidecar</span>
        <h3>The database behind localhost</h3>
        <p>A workload behind a Cloud SQL proxy sees <code>localhost:5432</code>, which every
        correct scanner suppresses as loopback. The real instance is named only in the
        sidecar's arguments, as <code>project:region:instance</code>.</p>
      </div>
      <div class="cell">
        <span class="tag">secret-ref</span>
        <h3>The connection string in a Secret</h3>
        <p>A workload mounting <code>orders-db-creds</code> is an unresolved blind spot. When an
        ACK, Crossplane or Config Connector resource in the same scan names that Secret,
        Reachmap resolves it to the actual RDS instance &mdash; without ever reading the Secret.</p>
      </div>
      <div class="cell">
        <span class="tag">workload-identity</span>
        <h3>The role a workload assumes</h3>
        <p>IRSA, GKE Workload Identity and their Azure equivalent are declared
        workload&rarr;cloud edges sitting in the manifest. The landscape survey found no
        vendor documenting them. They are also what an IAM-policy expansion needs first.</p>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sec-label">In CI</div>
    <h2>Gate the pull request that adds a dependency</h2>
    <p class="sec-intro">
      Scanning is useful once. Diffing is useful every day. Reachmap compares the graph on a
      branch against the graph on main and fails the build when a change quietly introduces a
      new third-party API, a new cloud service, or a dependency nobody has classified.
    </p>

    {term("reachmap diff", colorize(DIFF_OUTPUT))}

    <div class="grid grid-3">
      <div class="cell">
        <h3>Removals never fail</h3>
        <p>Every gate fires only on <em>added</em> dependencies. Dropping one is cleanup, and a
        tool that fails CI for it would punish exactly the change teams should be making.</p>
      </div>
      <div class="cell">
        <h3>Findings get their own exit code</h3>
        <p><code>0</code> clean, <code>1</code> tool error, <code>2</code> usage, <code>3</code>
        findings. Collapsing findings into <code>1</code> makes a crash indistinguishable from a
        tripped gate, and those need different responses at 3am.</p>
      </div>
      <div class="cell">
        <h3>Output CI already reads</h3>
        <p>A markdown comment for the pull request, SARIF for the security tab, Graphviz DOT
        and Backstage catalog entities for everything downstream.</p>
      </div>
    </div>
    <p style="margin-top:1.5rem"><a href="docs/ci.html">Set up the gate &rarr;</a></p>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sec-label">Design</div>
    <h2>Three decisions that shape everything else</h2>
    <div class="grid grid-3">
      <div class="cell">
        <h3>Every edge carries its evidence</h3>
        <p>File, line, field, and the redacted snippet it came from. A tool that cannot answer
        <em>says who?</em> gets abandoned the first time it surprises someone. Credentials are
        stripped at parse time, before anything reaches the graph.</p>
      </div>
      <div class="cell">
        <h3>Precision over recall</h3>
        <p>A graph people believe beats a graph that is complete. <code>LOG_LEVEL=info</code> does
        not become a dependency on a service called &ldquo;info&rdquo;. Bare tokens count only when
        the key they sit under says so.</p>
      </div>
      <div class="cell">
        <h3>Confidence is a bucket, not a float</h3>
        <p><code>confirmed</code> / <code>likely</code> / <code>possible</code>. An edge a user
        disagrees with has to be arguable, and &ldquo;0.73&rdquo; is not an argument.</p>
      </div>
    </div>

    <div class="note">
      <strong>Blind spots are counted, not hidden.</strong> When a connection string lives in a
      Secret that nothing in the scan describes, Reachmap records that a dependency exists and
      that it cannot see the target. A blind spot you can count is one you can argue about.
      Cluster mode does not change this: it never reads Secrets either.
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sec-label">Install</div>
    <h2>One binary, one vendored dependency</h2>
    <p class="sec-intro">
      Reachmap is Go with a single vendored dependency &mdash; a YAML parser &mdash; so it builds
      offline, audits in an afternoon and ships as one static binary.
    </p>

    {term("build from source", colorize('''$ git clone https://github.com/reachmap/reachmap.dev
$ cd reachmap.dev
$ go build -mod=vendor -o reachmap ./cmd/reachmap
$ ./reachmap scan ./manifests'''))}

    <div class="note warn">
      <strong>A note on <code>go install</code>.</strong> The module path is
      <code>reachmap.dev</code>, which needs that domain to serve a <code>go-import</code> meta
      tag before <code>go install reachmap.dev/cmd/reachmap@latest</code> can resolve. The tag is
      already in this site's HTML, so it starts working the moment the domain points here.
      Until then, build from source.
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sec-label">Roadmap</div>
    <h2>Where this is going</h2>
    <div class="table-scroll">
      <table>
        <thead><tr><th>Phase</th><th>Scope</th><th>Status</th></tr></thead>
        <tbody>
          <tr><td><code>v0.1</code></td><td>Manifest detectors, endpoint catalog, ARN/DSN parsers, JSON + Mermaid + text</td><td>Shipped</td></tr>
          <tr><td><code>v0.2</code></td><td><code>diff</code>, <code>policy check</code>, SARIF/DOT/Backstage exporters, GitHub Action</td><td>Shipped</td></tr>
          <tr><td><code>v0.3</code></td><td>Mesh, KEDA, cloud resource CRs, External Secrets, workload identity, storage, registries; live cluster mode; full GCP + Azure</td><td>Shipped</td></tr>
          <tr><td><code>v0.4</code></td><td>IAM policy expansion &mdash; resolve an identity into the resources it may reach</td><td>Next</td></tr>
          <tr><td><code>v0.5</code></td><td>Runtime adapters (Hubble, Coroot, OTel, VPC/DNS logs); shadow and stale reports</td><td>Planned</td></tr>
          <tr><td><code>v0.6</code></td><td>Source-code scanning: Go, Java, Python, Node</td><td>Planned</td></tr>
          <tr><td><code>v1.0</code></td><td>Blast-radius traversal with criticality, environment diffing, <code>reachmap serve</code></td><td>Planned</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sec-label">Known limits</div>
    <h2>Stated plainly</h2>
    <p class="sec-intro">
      A tool that overclaims here loses trust the first time it is wrong.
    </p>
    <ul style="color:var(--fg-mute); max-width:46rem; line-height:1.8">
      <li><strong>Secrets.</strong> A connection string in a Secret is invisible unless something in
      the scan describes that Secret. Reachmap does not read Secrets, in cluster mode either.</li>
      <li><strong>Dynamically constructed endpoints.</strong>
      <code>os.getenv("REGION") + ".internal.foo.com"</code> cannot be resolved statically.</li>
      <li><strong>Unrendered templates.</strong> Refused with a message rather than scanned, because
      analysing them produces dependencies on literal <code>&#123;&#123; .Values.host &#125;&#125;</code> strings.</li>
      <li><strong>Permitted reach is not observed reach.</strong> Mesh and network-policy edges say a
      workload <em>may</em> reach something. Proving it does needs runtime data.</li>
    </ul>
  </div>
</section>

</main>
"""
        + footer(rel)
    )


# ---------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------

def docs_overview():
    body = f"""
<p>Reachmap answers four questions about a service estate, and the documentation is
organised around them.</p>

<div class="grid grid-2" style="margin:1.5rem 0 2rem">
  <div class="cell">
    <h3><a href="quickstart.html">Quickstart</a></h3>
    <p>Build it, scan a directory, read the output, pick a format. Ten minutes.</p>
  </div>
  <div class="cell">
    <h3><a href="detectors.html">Detectors</a></h3>
    <p>Every signal Reachmap reads, what confidence each earns, and why a permitted
    edge is not a declared one.</p>
  </div>
  <div class="cell">
    <h3><a href="cluster.html">Cluster mode</a></h3>
    <p>Reading a live cluster through <code>kubectl</code>, the RBAC it needs, and why it
    never reads Secrets.</p>
  </div>
  <div class="cell">
    <h3><a href="ci.html">CI &amp; policy</a></h3>
    <p>Diffing two graphs, the dependency gates, the GitHub Action, and governance rules
    as data.</p>
  </div>
</div>

<h2>The model in one page</h2>

<p>A scan produces a <strong>graph</strong>. Nodes are workloads, internal services,
datastores, cloud resources, external APIs, cloud identities, and opaque secret references.
Edges carry a relation, a protocol and port where known, a confidence bucket, and one or
more pieces of evidence.</p>

<h3>Node kinds</h3>
<div class="table-scroll">
<table>
  <thead><tr><th>Kind</th><th>What it is</th></tr></thead>
  <tbody>
    <tr><td><code>Workload</code></td><td>A Deployment, StatefulSet, DaemonSet, Job, CronJob, Pod or Argo Rollout</td></tr>
    <tr><td><code>InternalService</code></td><td>A Service in the scanned set</td></tr>
    <tr><td><code>Datastore</code></td><td>A Service fronting a self-hosted database &mdash; deliberately <em>not</em> the same node kind as a managed one</td></tr>
    <tr><td><code>CloudResource</code></td><td>A named cloud resource. Identified by its native ARN where one exists</td></tr>
    <tr><td><code>ExternalAPI</code></td><td>A third-party endpoint</td></tr>
    <tr><td><code>Identity</code></td><td>An IAM role, GCP service account or Azure client id a workload assumes</td></tr>
    <tr><td><code>OpaqueSecretRef</code></td><td>A dependency that provably exists but whose target is in a Secret</td></tr>
  </tbody>
</table>
</div>

<h3>Relations</h3>
<p>The relation is the difference between &ldquo;this workload talks to X&rdquo; and &ldquo;this
workload is <em>allowed</em> to talk to X&rdquo;, and conflating them inflates every graph in a
mesh-heavy estate.</p>
<dl class="kv" style="margin:1rem 0 1.5rem">
  <dt>declared</dt><dd>The manifest states the dependency &mdash; an env var, an argument, a trigger.</dd>
  <dt>allowed</dt><dd>A mesh entry or network policy <em>permits</em> reach. Nothing proves it is used.</dd>
  <dt>selects</dt><dd>A structural Service&rarr;workload mapping. Excluded from diffs and gates.</dd>
  <dt>referenced</dt><dd>Found in source code. Reserved for a later release.</dd>
  <dt>observed</dt><dd>Seen in runtime telemetry. Reserved for a later release.</dd>
</dl>

<h3>Confidence</h3>
<div class="table-scroll">
<table>
  <thead><tr><th>Bucket</th><th>Earned by</th></tr></thead>
  <tbody>
    <tr><td><code>confirmed</code></td><td>The manifest names the target outright: a literal ARN, an <code>ExternalName</code>, hand-written Endpoints, a structural selector match, a ServiceAccount annotation naming a role, a proxy argument naming an instance, a StorageClass provisioner, a <code>SecretStore</code> naming its backend, an operator-written connection Secret</td></tr>
    <tr><td><code>likely</code></td><td>An endpoint parsed from config that matched a catalog rule, or a resource joined through a shared credential Secret</td></tr>
    <tr><td><code>possible</code></td><td>An endpoint no rule recognises, or a dependency whose target is in a Secret</td></tr>
  </tbody>
</table>
</div>

<h2>Exit codes</h2>
<dl class="kv">
  <dt>0</dt><dd>Clean.</dd>
  <dt>1</dt><dd>Tool error &mdash; something broke.</dd>
  <dt>2</dt><dd>Usage error &mdash; bad flags or arguments.</dd>
  <dt>3</dt><dd>Findings &mdash; a dependency gate tripped or a policy rule fired.</dd>
</dl>
<p>Findings get their own code on purpose. Collapsing them into <code>1</code>, which is the
common convention, makes a crash look identical to a tripped gate, and those need different
responses from whoever is on call.</p>
"""
    return doc_page("index", "Documentation",
                    "What Reachmap produces, and how to read it.",
                    body,
                    "Reachmap documentation: the graph model, node kinds, relations, "
                    "confidence buckets and exit codes.")


def docs_quickstart():
    body = f"""
<h2>Build it</h2>
<p>Reachmap is Go 1.22 with one vendored dependency, so it builds offline and needs no
module proxy.</p>

{term("build", colorize('''$ git clone https://github.com/reachmap/reachmap.dev
$ cd reachmap.dev
$ go build -mod=vendor -o reachmap ./cmd/reachmap
$ ./reachmap version'''))}

<div class="note warn">
<strong><code>go install</code> is not available yet.</strong> The module path is
<code>reachmap.dev</code>, and Go resolves a vanity path by fetching a
<code>go-import</code> meta tag from that domain. The tag is served by this site, but the
domain is not yet pointed at it, so <code>go install reachmap.dev/cmd/reachmap@latest</code>
cannot resolve. Build from source until then.
</div>

<h2>Scan a directory</h2>
<p>Point it at rendered Kubernetes manifests &mdash; a directory, a single file, or
<code>-</code> for stdin.</p>

{term("scan", colorize('''$ reachmap scan ./manifests
$ reachmap scan ./deploy/prod.yaml -env prod
$ cat prod.yaml | reachmap scan -'''))}

<h3>Helm and Kustomize must be rendered first</h3>
<p>Reachmap refuses unrendered templates rather than scanning them. Analysing a template
produces dependencies on literal <code>&#123;&#123; .Values.host &#125;&#125;</code> strings, which is worse
than scanning nothing &mdash; it looks like data.</p>

{term("render first", colorize('''$ helm template . -f values-prod.yaml | reachmap scan - -env prod
$ kustomize build overlays/prod | reachmap scan -'''))}

<h2>Read the output</h2>
<p>Each line under a workload is one dependency. The bracketed terms are the protocol and
port where known, the confidence bucket, the relation when it is not a plain declaration,
and the target's category and compliance scope. The line beneath is the evidence: the file,
the line, and the exact field.</p>

{term("one edge, annotated", colorize('''    -> [cloud]    gcp sql analytics-primary  [postgres, confirmed, database]
       platform.yaml:46  spec.template.spec.containers[cloud-sql-proxy].args[1]'''))}

<p>Read that as: the <code>ingestor</code> workload reaches a GCP Cloud SQL instance named
<code>analytics-primary</code> over Postgres; the claim is <code>confirmed</code> because the
manifest names the instance outright; and you can verify it at line 46 of
<code>platform.yaml</code>, in the second argument of the <code>cloud-sql-proxy</code>
container.</p>

<h2>Pick a format</h2>
<div class="table-scroll">
<table>
  <thead><tr><th>Flag</th><th>Output</th><th>For</th></tr></thead>
  <tbody>
    <tr><td><code>-format text</code></td><td>The annotated tree above</td><td>Reading it yourself (default)</td></tr>
    <tr><td><code>-format json</code></td><td>The full graph with all evidence</td><td>Diffing, policy, anything downstream</td></tr>
    <tr><td><code>-format mermaid</code></td><td>Mermaid <code>flowchart</code></td><td>Dropping into a README or a doc</td></tr>
    <tr><td><code>-format dot</code></td><td>Graphviz DOT</td><td>Rendering a real diagram</td></tr>
  </tbody>
</table>
</div>

<p><code>reachmap export</code> converts a saved JSON graph into the rest:
<code>backstage</code> catalog entities, plus all of the above.</p>

<h2>Useful flags</h2>
<dl class="kv">
  <dt>-o, -out FILE</dt><dd>Write to a file instead of stdout.</dd>
  <dt>-env NAME</dt><dd>Stamp an environment label on every edge, so two environments can be compared later.</dd>
  <dt>-cluster NAME</dt><dd>Cluster name used in node identities, so two clusters never collide in a merged graph.</dd>
  <dt>-include-opaque</dt><dd>Keep secret-borne placeholder nodes. On by default &mdash; the blind spot should be visible.</dd>
  <dt>-quiet</dt><dd>Suppress warnings on stderr.</dd>
</dl>

<h2>What to do next</h2>
<p>Two things are worth doing on the first real scan. Look at the unclassified endpoints
Reachmap reports at the bottom &mdash; each one is a triage item nobody has reviewed, and a
<a href="catalog.html">catalog rule</a> waiting to be written. Then
<a href="ci.html">wire up the pull-request gate</a>, which is what turns a one-off scan into
something that keeps working.</p>
"""
    return doc_page("quickstart", "Quickstart",
                    "Build it, scan a directory, and read what comes out.",
                    body,
                    "Build Reachmap from source, scan rendered Kubernetes manifests, "
                    "and read the annotated dependency output.")


GATE_WORKFLOW = """name: Dependency gate
on: pull_request

permissions:
  contents: read
  pull-requests: write
  security-events: write

jobs:
  reachmap:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # the diff needs the base commit

      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'

      - id: reachmap
        uses: reachmap/reachmap.dev@v0
        continue-on-error: true   # comment first, fail the job at the end
        with:
          path: manifests
          base-ref: origin/${{ github.base_ref }}
          environment: prod
          fail-on: new-external,new-unclassified,new-compliance

      - name: Comment on the pull request
        if: always() && hashFiles('reachmap-out/diff.md') != ''
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          header: reachmap
          path: reachmap-out/diff.md

      - name: Upload policy findings
        if: always() && hashFiles('reachmap-out/policy.sarif') != ''
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: reachmap-out/policy.sarif
          category: reachmap-policy

      - name: Fail if a gate tripped
        if: steps.reachmap.outcome == 'failure'
        run: exit 1"""


def docs_detectors():
    body = f"""
<p>A detector is one signal Reachmap reads. Each one is named in the evidence on every edge
it produces, so an edge you disagree with can be traced to the exact rule that made it.</p>

<h2>Layer 0 &mdash; rendered manifests</h2>
<p>No cluster, no credentials, no network. This is the layer that runs on a pull request.</p>

<div class="table-scroll">
<table>
  <thead><tr><th>Detector</th><th>Reads</th><th>Why it earns its place</th></tr></thead>
  <tbody>
    <tr><td><code>env-var</code></td><td>Container <code>env</code> values</td><td>URLs, DSNs, hostnames and ARNs, with credentials stripped at parse time</td></tr>
    <tr><td><code>command-args</code></td><td><code>command</code> and <code>args</code></td><td>Endpoints reach containers this way as often as through env, especially for proxies</td></tr>
    <tr><td><code>configmap</code></td><td>ConfigMap contents</td><td>Attributed only to workloads that actually consume the key, so one shared ConfigMap does not smear across every workload</td></tr>
    <tr><td><code>secret-ref</code></td><td><code>secretKeyRef</code>, <code>envFrom</code>, secret volumes</td><td>Resolves against cloud resource CRs and secret stores; records what it cannot resolve</td></tr>
    <tr><td><code>external-name</code></td><td><code>Service type: ExternalName</code></td><td>An explicit CNAME is an unambiguous declaration</td></tr>
    <tr><td><code>external-endpoints</code></td><td>Hand-written <code>Endpoints</code> / <code>EndpointSlice</code></td><td>A selector-less Service with manual endpoints points somewhere real</td></tr>
    <tr><td><code>service-selector</code></td><td>Service selectors</td><td>Structural Service&rarr;workload mapping; excluded from diffs and gates</td></tr>
    <tr><td><code>keda-trigger</code></td><td>KEDA <code>ScaledObject</code> / <code>ScaledJob</code></td><td>The highest-precision detector: the trigger names the queue, <code>scaleTargetRef</code> names the workload</td></tr>
    <tr><td><code>istio-serviceentry</code></td><td>Istio <code>ServiceEntry</code></td><td>External hosts the mesh permits</td></tr>
    <tr><td><code>mesh-routing</code></td><td><code>VirtualService</code>, Gateway API <code>HTTPRoute</code></td><td>Routing destinations outside the scanned set</td></tr>
    <tr><td><code>netpol-egress</code></td><td>Kubernetes and Cilium egress policy</td><td>Named hosts and specific addresses a workload may reach</td></tr>
    <tr><td><code>workload-identity</code></td><td>ServiceAccount annotations</td><td>IRSA, GKE Workload Identity, Azure workload identity</td></tr>
    <tr><td><code>proxy-sidecar</code></td><td>Cloud SQL and AlloyDB proxy arguments</td><td>The only place the instance is named when the app sees <code>localhost</code></td></tr>
    <tr><td><code>secret-backend</code></td><td>External Secrets Operator, Secrets Store CSI</td><td>The store behind a Secret is itself a hard dependency</td></tr>
    <tr><td><code>storage</code></td><td>NFS, in-tree cloud volumes, PVC&rarr;StorageClass</td><td>A PVC on <code>ebs.csi.aws.com</code> ties a workload to one AZ in one account</td></tr>
    <tr><td><code>image-registry</code></td><td>Container image references</td><td>Always present, a real supply-chain dependency, almost never written down</td></tr>
  </tbody>
</table>
</div>

<p>Plus an ARN parser, a DSN/URI parser, in-cluster DNS resolution, and an
<a href="catalog.html">endpoint catalog</a> of 142 rules.</p>

<h2>Layer 1 &mdash; a live cluster</h2>
<p>The same detectors, run against objects read from a running cluster rather than a
directory. See <a href="cluster.html">cluster mode</a>.</p>

<h2>Permitted is not declared</h2>
<p>A mesh <code>ServiceEntry</code> or an egress policy says a workload <em>may</em> reach
something. Modelling that as a declaration would inflate every graph in a mesh-heavy estate
with dependencies nobody uses, so those edges carry the relation <code>allowed</code> and the
text output names it.</p>

<p>This has a consequence that matters more than it sounds. The default policy's
<code>hardcoded-ip-dependency</code> and <code>unclassified-external-endpoint</code> rules are
scoped to <code>declared</code> edges &mdash; because a NetworkPolicy egress rule can
<em>only</em> be written as a CIDR. Erroring on one would penalise the single place where an
IP literal is the correct answer, and a gate that fires on your security controls is a gate
people learn to ignore.</p>

<h3>Wide CIDRs are not nodes</h3>
<p>Only <code>/32</code> and <code>/128</code> are specific enough to name a dependency. A
<code>10.0.0.0/8</code> egress rule describes a network boundary, not a thing something
depends on.</p>

<h2>Resolving a secret without reading it</h2>
<p>A workload mounting <code>orders-db-creds</code> is, on its own, an
<code>OpaqueSecretRef</code>: a dependency that provably exists with a target nobody can name.
Two things in the same scan can resolve it, and they are not equally strong:</p>

<div class="table-scroll">
<table>
  <thead><tr><th>Join</th><th>What it means</th><th>Confidence</th></tr></thead>
  <tbody>
    <tr><td><code>writeConnectionSecretToRef</code></td><td>The operator fills the Secret with the endpoint. A workload mounting it is talking to that resource.</td><td><code>confirmed</code></td></tr>
    <tr><td><code>masterUserPassword</code> (ACK)</td><td>The CR <em>reads</em> a password from the Secret. A workload reading the same Secret is a strong inference, not a proof.</td><td><code>likely</code></td></tr>
  </tbody>
</table>
</div>

<p>When neither applies, an <code>ExternalSecret</code> still names the store and the remote
path. &ldquo;This value comes from Vault at <code>platform/ingestor/stripe-token</code>&rdquo; is not
an endpoint, but it is enough for a person to find one &mdash; a materially different state
from &ldquo;this is a secret&rdquo;.</p>

<h2>What is deliberately suppressed</h2>
<p>Suppressed targets are counted in the scan summary rather than silently dropped, so the
count is auditable.</p>
<ul>
  <li><code>localhost</code> and loopback addresses &mdash; not a dependency on anything external.</li>
  <li><code>example.com</code>, <code>example.org</code> and friends &mdash; placeholders.</li>
  <li>Unrendered template expressions.</li>
  <li>Private IP ranges, which are recorded but not classified as external APIs.</li>
  <li>Bare tokens under keys that do not suggest an endpoint &mdash; this is what stops
  <code>LOG_LEVEL=info</code> becoming a dependency on a service called &ldquo;info&rdquo;.</li>
</ul>

<h2>In-cluster resolution beats the catalog</h2>
<p>A cluster-local Service named <code>s3</code> is not Amazon S3. And a name like
<code>orders-db.shop</code> is an in-cluster reference, not a <code>.shop</code> domain &mdash;
namespace names collide with real gTLDs (<code>shop</code>, <code>app</code>, <code>dev</code>,
<code>cloud</code>) more often than you would like. Reachmap resolves against the Services it
actually saw before it consults any rule.</p>
"""
    return doc_page("detectors", "What Reachmap detects",
                    "Every signal it reads, what each one earns, and what it refuses to guess.",
                    body,
                    "The full Reachmap detector table: manifest signals, mesh and policy "
                    "edges, secret resolution, and what is deliberately suppressed.")


def docs_cluster():
    body = f"""
<p>Cluster mode reads live objects instead of a directory. Everything else &mdash; the
detectors, the catalog, the output formats &mdash; is identical.</p>

{term("scan a cluster", colorize('''$ reachmap scan @cluster
$ reachmap scan @cluster -context prod-eu -namespace payments
$ reachmap scan @cluster -namespace payments -namespace checkout -format json -o prod.json'''))}

<h2>It never reads Secrets</h2>
<div class="note">
This is a product invariant, not a default. Reachmap records that a secret-borne dependency
exists and resolves it through the objects that <em>describe</em> the Secret &mdash; a cloud
resource CR, an <code>ExternalSecret</code> &mdash; never by reading the credential itself.
A test enforces it.
</div>

<p>The original design for this layer proposed reading Secrets, classifying the value, and
discarding it. That is now recorded as rejected. A dependency mapper that pulls plaintext
credentials out of a production cluster is a credential-exfiltration tool wearing a different
hat, and &ldquo;we discard it&rdquo; is a promise about code that an operator cannot verify at
the moment they are being asked to grant the RBAC.</p>

<h2>Why <code>kubectl</code> and not client-go</h2>
<p>This is the largest architectural decision in cluster mode, and it was not close.</p>
<p>Linking <code>client-go</code> would add roughly fifty modules to a project whose only
vendored dependency is a YAML parser &mdash; and that property is load-bearing: Reachmap
builds offline, audits in an afternoon, and ships as one static binary. Shelling out also
inherits, for free, everything a library would have to reimplement: kubeconfig contexts, exec
credential plugins for EKS, GKE and AKS, proxies, and impersonation.</p>
<p>The cost is a runtime dependency on a binary and on its JSON output shape, which is a
stable versioned API. That is the smaller risk.</p>

<h2>What it reads</h2>
<p>Requests are filtered against what the API server actually serves, so a cluster without
Istio or KEDA costs nothing. Nothing is read speculatively &mdash; on a large cluster each
extra kind is a real list request.</p>
<ul>
  <li><strong>Workloads and routing:</strong> Deployments, StatefulSets, DaemonSets, CronJobs,
  Jobs, Services, Ingresses, ConfigMaps, ServiceAccounts, PVCs, StorageClasses, NetworkPolicies</li>
  <li><strong>Mesh and gateway:</strong> Istio <code>ServiceEntry</code>, <code>VirtualService</code>,
  <code>DestinationRule</code>, <code>Sidecar</code>; Gateway API <code>HTTPRoute</code> and
  <code>Gateway</code>; <code>CiliumNetworkPolicy</code></li>
  <li><strong>Autoscaling:</strong> KEDA <code>ScaledObject</code> and <code>ScaledJob</code></li>
  <li><strong>Secret plumbing:</strong> <code>ExternalSecret</code>, <code>SecretStore</code>,
  <code>ClusterSecretStore</code>, <code>SecretProviderClass</code> &mdash; the objects that
  describe Secrets, never Secrets</li>
  <li><strong>Argo:</strong> <code>Rollout</code></li>
</ul>

<h2>Partial visibility is the normal case</h2>
<p>A scoped service account will not be able to list everything, and that is fine. If a
batched read is refused, Reachmap retries the kinds one at a time, so one RBAC gap costs one
resource rather than the whole scan. Each miss becomes a warning on stderr.</p>

<h3>A read-only role</h3>
{term("rbac.yaml", colorize('''apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata: {name: reachmap-reader}
rules:
  - apiGroups: ["", "apps", "batch", "networking.k8s.io", "storage.k8s.io"]
    resources: ["*"]
    verbs: ["get", "list"]
  - apiGroups: ["networking.istio.io", "keda.sh", "external-secrets.io",
                "gateway.networking.k8s.io", "cilium.io", "argoproj.io",
                "secrets-store.csi.x-k8s.io"]
    resources: ["*"]
    verbs: ["get", "list"]
'''), copy=True)}

<div class="note warn">
The wildcard in the first rule includes <code>secrets</code>. Reachmap will not request them,
but if your policy is that a credential a process could read is a credential it has, enumerate
the resources explicitly instead of using <code>"*"</code>.
</div>

<h2>Evidence from a cluster has no line numbers</h2>
<p>&ldquo;Line 8412 of the JSON <code>kubectl</code> printed&rdquo; is not something anyone can
act on. Each live object becomes its own source &mdash;
<code>cluster://context/namespace/Kind/name</code> &mdash; and the field path carries the
precision the line number used to.</p>

{term("cluster evidence", colorize('''    -> [cloud]    aws rds orders-prod  [postgres/5432, likely, database]
       cluster://prod-eu/shop/Deployment/orders  spec.template.spec.containers[app].env[DATABASE_URL]'''))}

<h2>L1 is a stronger claim than L0</h2>
<p>The same detectors read the same fields either way, but a manifest says what someone
intends to deploy and a cluster read says what is running. Evidence from cluster mode is
stamped <code>L1</code> to preserve that difference.</p>

<h2>Flags</h2>
<dl class="kv">
  <dt>-context NAME</dt><dd>kubeconfig context. Defaults to the current one, whose name also becomes the cluster identity.</dd>
  <dt>-namespace NS</dt><dd>Restrict to a namespace. Repeatable; default is all namespaces.</dd>
  <dt>-kubectl PATH</dt><dd>Which <code>kubectl</code> to use.</dd>
  <dt>-timeout DURATION</dt><dd>Per-request timeout. Default 2 minutes.</dd>
</dl>
"""
    return doc_page("cluster", "Cluster mode",
                    "Reading a live cluster through kubectl &mdash; and why it never reads Secrets.",
                    body,
                    "Reachmap cluster mode: scanning live Kubernetes objects via kubectl, "
                    "the RBAC it needs, and the invariant that it never reads Secrets.")


def docs_ci():
    workflow = term(".github/workflows/dependency-gate.yml", colorize(GATE_WORKFLOW))
    body = f"""
<p>Scanning tells you what you have. Diffing tells you what a change is about to add, which
is the thing you can still do something about.</p>

<h2>Diff two graphs</h2>
{term("reachmap diff", colorize(DIFF_OUTPUT))}

<p>Graphs are matched on <code>(from, to, relation)</code>. A change to a dependency's port or
protocol is the same dependency with a different detail, so it surfaces as a <em>changed</em>
edge rather than as a removal plus an addition &mdash; otherwise the real signal gets buried in
a busy diff.</p>

<h3>Gates</h3>
<p><code>-fail-on</code> takes one or more of these. All of them fire only on <strong>added</strong>
dependencies.</p>
<div class="table-scroll">
<table>
  <thead><tr><th>Gate</th><th>Trips when the change adds&hellip;</th></tr></thead>
  <tbody>
    <tr><td><code>none</code></td><td>Never. Report only.</td></tr>
    <tr><td><code>any</code></td><td>Any change at all, including a changed detail.</td></tr>
    <tr><td><code>new-dependency</code></td><td>Any new edge.</td></tr>
    <tr><td><code>new-external</code></td><td>A third-party API.</td></tr>
    <tr><td><code>new-cloud</code></td><td>A cloud resource.</td></tr>
    <tr><td><code>new-unclassified</code></td><td>An endpoint no catalog rule recognises.</td></tr>
    <tr><td><code>new-compliance</code></td><td>A dependency in a regulated scope (PCI, PII).</td></tr>
    <tr><td><code>new-secret-borne</code></td><td>A dependency whose target is invisible.</td></tr>
  </tbody>
</table>
</div>

<p>A good first gate is <code>new-external,new-unclassified</code>: it catches the two changes
a reviewer most wants to be told about and almost never fires on routine work.</p>

<h3>Formats</h3>
<p><code>-format markdown</code> is shaped as a pull-request comment.
<code>-format sarif</code> uploads to the GitHub security tab. <code>text</code> and
<code>json</code> are also available.</p>

<h2>The GitHub Action</h2>
{workflow}

<p>The <code>continue-on-error</code> plus explicit final step is deliberate: a contributor
should see the comment explaining <em>why</em> the build failed, not just a red X.</p>

<div class="note warn">
The action installs Reachmap with <code>go install reachmap.dev/cmd/reachmap@latest</code>,
which needs the <code>reachmap.dev</code> domain to resolve first. Until then, build the
binary in a prior step and point the action at it.
</div>

<h2>Policy as data</h2>
<p><code>reachmap policy check</code> evaluates governance rules against a saved graph.
Rules live in <code>.reachmap/policy.yaml</code>; a commented starter policy ships with the
repository.</p>

{term("reachmap policy check", colorize(POLICY_OUTPUT))}

<h3>Writing a rule</h3>
{term(".reachmap/policy.yaml", colorize('''rules:
  # Ban a category, name the approved exceptions. This is how governance rules
  # actually get adopted.
  - id: unapproved-payment-processor
    description: Payment traffic must go through the approved processor.
    severity: error
    match:
      edge:
        relation: [declared]
        to:
          category: [payments]
    except: ["api.stripe.com"]

  # A budget rather than a ban. Fires only on the overage.
  - id: external-api-budget
    description: More third-party APIs than this estate has agreed to carry.
    severity: warn
    match:
      node:
        kind: [ExternalAPI]
    max_count: 15'''))}

<p>Matchers only express what the graph actually knows &mdash; no annotation lookups, no
manifest re-reads. A rule that appeared to check something the graph cannot see would be worse
than no rule at all, because it would pass silently.</p>

<h3>Matcher fields</h3>
<dl class="kv">
  <dt>node</dt><dd><code>kind</code>, <code>classified</code>, <code>category</code>, <code>compliance</code>, <code>provider</code>, <code>service</code>, <code>vendor</code>, <code>namespace</code>, <code>name</code> (regex)</dd>
  <dt>edge</dt><dd><code>relation</code>, <code>protocol</code>, <code>confidence</code>, <code>port</code>, <code>crosses_namespace</code>, plus <code>from</code> and <code>to</code> node matchers</dd>
  <dt>max_count</dt><dd>Turns the rule into a budget; reports only the overage.</dd>
  <dt>except</dt><dd>Allowlist. Every list is an OR; every field within a matcher is an AND.</dd>
</dl>

<p><code>-fail-on</code> sets the severity at or above which findings fail the build:
<code>error</code>, <code>warn</code> or <code>none</code>.</p>

<h2>Exporting to other tools</h2>
<div class="table-scroll">
<table>
  <thead><tr><th>Format</th><th>Goes to</th></tr></thead>
  <tbody>
    <tr><td><code>sarif</code></td><td>The GitHub security tab, or any SARIF viewer</td></tr>
    <tr><td><code>backstage</code></td><td>Backstage catalog entities &mdash; Components and Resources with <code>dependsOn</code></td></tr>
    <tr><td><code>dot</code></td><td>Graphviz</td></tr>
    <tr><td><code>mermaid</code></td><td>A README or a doc</td></tr>
  </tbody>
</table>
</div>
"""
    return doc_page("ci", "Gating a pull request",
                    "Diff two graphs, fail on what got added, and evaluate policy as data.",
                    body,
                    "Reachmap in CI: dependency diffs, gates, the GitHub Action, "
                    "policy rules as data, and SARIF output.")


def docs_catalog():
    rule_simple = term("internal/catalog/data/thirdparty.yaml", colorize(
        "- id: vendor.riskscore\n"
        "  kind: external\n"
        "  vendor: RiskScore\n"
        "  category: fraud\n"
        "  compliance: [pii]\n"
        "  priority: 80\n"
        "  match: '^api\\.riskscore\\.io$'\n"
        "  name: RiskScore"))
    rule_cloud = term("a cloud rule with identity", colorize(
        "- id: aws.rds.instance\n"
        "  kind: cloud\n"
        "  provider: aws\n"
        "  service: rds\n"
        "  resource_type: db\n"
        "  category: database\n"
        "  priority: 85\n"
        "  match: '^(?P<name>[a-z0-9-]+)\\.(?P<uid>[a-z0-9]+)\\."
        "(?P<region>[a-z0-9-]+)\\.rds\\.amazonaws\\.com$'\n"
        "  identity: 'arn:aws:rds:{region}:{account}:db:{name}'\n"
        "  name: '{name}'\n"
        "  protocol: postgres\n"
        "  default_port: 5432"))
    lint = term("check your rule", colorize(
        "$ reachmap catalog lint\n"
        "catalog OK: 142 rules compiled\n"
        "\n"
        "$ reachmap catalog explain api.riskscore.io"))
    body = f"""
<p>The catalog is what turns <code>b-1.events.abc123.c2.kafka.eu-west-1.amazonaws.com</code>
into &ldquo;the MSK cluster <code>events</code>, messaging, AWS, eu-west-1&rdquo;. It is data, not
code: 142 rules across five YAML files, embedded in the binary at build time.</p>

<div class="table-scroll">
<table>
  <thead><tr><th>File</th><th>Rules</th><th>Covers</th></tr></thead>
  <tbody>
    <tr><td><code>aws.yaml</code></td><td>36</td><td>RDS, S3, SQS, SNS, MSK, ElastiCache, ECR, OpenSearch, DynamoDB, Secrets Manager&hellip;</td></tr>
    <tr><td><code>gcp.yaml</code></td><td>26</td><td>Cloud SQL, Spanner, Firestore, Bigtable, Pub/Sub, GCS, Artifact Registry, Secret Manager&hellip;</td></tr>
    <tr><td><code>azure.yaml</code></td><td>21</td><td>Azure SQL, Cosmos, Service Bus, Key Vault, Blob, ACR, Entra ID, Azure Monitor&hellip;</td></tr>
    <tr><td><code>managed.yaml</code></td><td>17</td><td>Managed data platforms and the instance metadata service</td></tr>
    <tr><td><code>thirdparty.yaml</code></td><td>42</td><td>Payments, auth, observability, email, AI APIs</td></tr>
  </tbody>
</table>
</div>

<h2>Unclassified is an output, not a failure</h2>
<p>An endpoint no rule recognises is reported, counted, and listed at the end of a scan.
Each one is a triage item for a security review and a catalog contribution waiting to happen.
Hiding them would make the tool look more complete and be less useful.</p>

<p>Bare IP addresses are reported separately, because no catalog keyed on hostnames can ever
name one &mdash; &ldquo;add a rule for <code>52.31.44.7</code>&rdquo; is advice nobody can act on.</p>

<h2>Adding a rule</h2>
{rule_simple}

<p>For a cloud resource, capture the identity out of the hostname so that two spellings of the
same thing converge on one node rather than duplicating it:</p>

{rule_cloud}

<h3>Fields</h3>
<dl class="kv">
  <dt>kind</dt><dd><code>cloud</code> or <code>external</code>.</dd>
  <dt>match</dt><dd>A regular expression. Tested against the host by default; set <code>match_on: url</code> when the identity lives in the path, as it does for SQS.</dd>
  <dt>priority</dt><dd>Higher wins. Specific rules sit above the per-provider fallbacks, which are deliberately low.</dd>
  <dt>identity</dt><dd>A template producing a native identifier &mdash; an ARN. Used as the node URN, so a hostname match and an ARN match converge.</dd>
  <dt>name</dt><dd>A template over the named capture groups.</dd>
  <dt>category, compliance</dt><dd>What the endpoint is, and what regulated scope it sits in. <code>compliance</code> is what the <code>new-compliance</code> gate reads.</dd>
  <dt>protocol, default_port</dt><dd>Annotate the edge when the source did not say.</dd>
</dl>

{lint}

<h2>One rule, one claim</h2>
<p>Two rules matching the same hostname pattern is an ambiguity dressed up as coverage.
Azure Event Hubs and Service Bus share the <code>*.servicebus.windows.net</code> zone and the
hostname genuinely does not say which service a namespace is, so the catalog reports a
messaging namespace and stops there. Guessing would be wrong half the time.</p>

<p>The same reasoning keeps the instance metadata address provider-neutral: AWS, Azure and GCP
all serve <code>169.254.169.254</code>, so labelling it as any one of them would be a guess.</p>
"""
    return doc_page("catalog", "The endpoint catalog",
                    "142 rules that turn a hostname into a named, categorised dependency.",
                    body,
                    "The Reachmap endpoint catalog: how hostnames are classified into named "
                    "cloud resources and third-party APIs, and how to add a rule.")


def main():
    write("index.html", landing())
    write("docs/index.html", docs_overview())
    write("docs/quickstart.html", docs_quickstart())
    write("docs/detectors.html", docs_detectors())
    write("docs/cluster.html", docs_cluster())
    write("docs/ci.html", docs_ci())
    write("docs/catalog.html", docs_catalog())
    write("404.html", not_found())


def not_found():
    rel = ""
    return (
        head("Not found — Reachmap", "That page does not exist.", rel)
        + header(rel, "")
        + """<main id="main" class="wrap" style="padding:6rem 0; text-align:center">
  <h1 style="font-size:2rem; margin-bottom:.75rem">404</h1>
  <p style="color:var(--fg-mute); margin-bottom:2rem">
    That page does not exist. Every edge in Reachmap carries its evidence; this link did not.
  </p>
  <div class="cta-row" style="justify-content:center">
    <a class="btn btn-primary" href="index.html">Overview</a>
    <a class="btn" href="docs/index.html">Documentation</a>
  </div>
</main>
"""
        + footer(rel)
    )


if __name__ == "__main__":
    main()
