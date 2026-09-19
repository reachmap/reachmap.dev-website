# reachmap.dev-website

The website for [Reachmap](https://github.com/reachmap/reachmap.dev) — a dependency
mapper for Kubernetes-native distributed systems.

Plain static HTML, no framework, no build step at deploy time. GitHub Pages serves
the files in this repository as they are.

## Layout

```
index.html            Landing page
404.html              Not-found page
docs/                 Quickstart, detectors, cluster mode, CI & policy, catalog
assets/               style.css, site.js, favicon.svg, og.png, icon-180.png
assets/fonts/         Inter and JetBrains Mono (variable woff2) + their OFL licences
tools/build.py        Generator — regenerates every HTML file from one template
tools/diagrams.py     The inline SVG diagrams
tools/checklinks.py   Internal link checker, run in CI
tools/make_images.py  Re-renders og.png and icon-180.png
```

## Typefaces

Inter and JetBrains Mono, both variable, both self-hosted from `assets/fonts/`
rather than fetched from a font CDN. 88KB for the pair, preloaded, with
`font-display: swap` so text is readable before they land. Both are SIL Open
Font License; the licences are alongside the files, which is what the OFL
requires when you redistribute.

Self-hosting rather than linking a CDN keeps the site on one origin, removes a
third-party request, and means it renders the same offline as online — matching
the tool it documents, which vendors its one dependency for the same reason.

## Editing

Six pages share one header, one footer and one nav. Keeping those in sync by hand
is how a site drifts, so the page bodies live in `tools/build.py` and the HTML is
generated from them. The generated HTML is committed, which is why deployment needs
no toolchain.

```bash
# edit the page body in tools/build.py, then
python3 tools/build.py
python3 tools/checklinks.py
git add -A && git commit -m "docs: ..."
```

CI fails the build if the committed HTML does not match what the generator produces,
so the two cannot silently diverge.

Editing `assets/style.css` needs no regeneration.

The social card and touch icon are rendered from the live stylesheet rather than
drawn by hand, so they cannot drift from the site's own type and palette:

```bash
pip install playwright && playwright install chromium
python3 tools/make_images.py
```

The outputs are committed, so this is only needed when the card's content or the
palette changes.

### Previewing

```bash
python3 -m http.server 8000
# http://localhost:8000
```

## Enabling GitHub Pages

One-time, in this repository:

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
   The workflow in `.github/workflows/pages.yml` does the rest on every push to `main`.
2. The site goes live at `https://reachmap.github.io/reachmap.dev-website/`.

`.nojekyll` is kept as insurance rather than a requirement: a workflow that uploads
a Pages artifact serves the files as they are and never runs Jekyll. It only starts
mattering if this repository is ever switched to publishing from a branch, where
Jekyll would otherwise drop any path beginning with an underscore.

## Pointing `reachmap.dev` at it

Not done yet — the domain does not currently resolve. This matters beyond
appearances: Reachmap's Go module path is `reachmap.dev`, and Go resolves a vanity
import path by fetching a `go-import` meta tag from that domain over HTTPS. Until
the domain serves it, `go install reachmap.dev/cmd/reachmap@latest` cannot work, and
neither can the GitHub Action, which uses `go install` to fetch the binary.

The meta tag is already in every page of this site:

```html
<meta name="go-import" content="reachmap.dev git https://github.com/reachmap/reachmap.dev">
```

So the sequence is:

1. Register `reachmap.dev`.
2. Point DNS at GitHub Pages — apex `A` records to `185.199.108.153`,
   `185.199.109.153`, `185.199.110.153`, `185.199.111.153` (and the matching `AAAA`
   records `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`,
   `2606:50c0:8003::153`), plus a `CNAME` record for `www` pointing at
   `reachmap.github.io`.
3. **Settings → Pages → Custom domain**, enter `reachmap.dev`, Save, then tick
   **Enforce HTTPS** once the certificate is issued (can take up to 24 hours).
4. Verify the vanity path resolves before tagging a release:

   ```bash
   curl -s "https://reachmap.dev/?go-get=1" | grep go-import
   GOPROXY=direct go install reachmap.dev/cmd/reachmap@latest
   ```

> **Do not add a `CNAME` file to this repository.** That step applies only to sites
> published from a branch. This site publishes from a GitHub Actions workflow, and
> GitHub ignores any `CNAME` file in that mode — the custom domain lives solely in
> Settings → Pages. A committed `CNAME` file here would do nothing except look
> authoritative and mislead whoever reads it next.

Every link in this site is relative, so it works unchanged at both the project URL
and the apex domain — no rebuild needed when the domain lands. The one exception
is `og:image`, which the Open Graph spec requires to be absolute: update the host
in `tools/build.py` and regenerate when the domain changes, or the social card
will keep pointing at the github.io URL.

### The other prerequisite

`go install` also requires that `github.com/reachmap/reachmap.dev` is **public**.
The module proxy fetches the repository anonymously; a private repository fails to
resolve no matter what the meta tag says.

## Licence

Apache-2.0, matching the tool.
