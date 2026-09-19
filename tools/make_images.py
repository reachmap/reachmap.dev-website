#!/usr/bin/env python3
"""Render the social card and the touch icon.

Kept as a script rather than a hand-made file so the card cannot quietly fall
out of step with the site's own typeface and palette — it is drawn with the
same stylesheet, in a real browser, and re-rendered by running this.

    python3 tools/make_images.py

Needs playwright (pip install playwright && playwright install chromium). The
outputs are committed, so nobody needs it to deploy or to edit the site.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CARD = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="assets/style.css">
<style>
  html,body{margin:0;width:1200px;height:630px;overflow:hidden}
  body{display:flex;flex-direction:column;justify-content:space-between;
       padding:72px 80px;background:#fff;
       background-image:radial-gradient(circle, var(--line) 1px, transparent 1px);
       background-size:32px 32px}
  .row{display:flex;align-items:center;gap:14px}
  .row svg{width:34px;height:34px;color:var(--accent)}
  .wm{font:600 32px/1 var(--sans);letter-spacing:-.03em;color:var(--fg-strong)}
  .ver{font:500 15px/1 var(--sans);color:var(--fg-mute);border:1px solid var(--line);
       border-radius:999px;padding:5px 11px}
  h1{font:600 74px/1.03 var(--sans);letter-spacing:-.045em;color:var(--fg-strong);
     margin:0;max-width:19ch}
  h1 span{color:var(--fg-faint)}
  p{font:400 25px/1.45 var(--sans);color:var(--fg-mute);margin:26px 0 0;max-width:30ch}
  .foot{display:flex;align-items:baseline;gap:20px;font:500 19px/1 var(--mono);
        color:var(--fg-faint)}
  .foot b{color:var(--fg-strong);font-weight:500}
</style></head><body>
  <div class="row">__LOGO__<span class="wm">reachmap</span><span class="ver">__VER__</span></div>
  <div>
    <h1>Know what your workloads <span>depend on.</span></h1>
    <p>Every cloud service, internal service and third-party API your
       Kubernetes workloads reach — with the file and line behind every claim.</p>
  </div>
  <div class="foot"><b>reachmap scan ./manifests</b><span>16 detectors · 142 catalog rules · 0 agents</span></div>
</body></html>"""


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright is required: pip install playwright && playwright install chromium")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build

    card = os.path.join(ROOT, "_card.html")
    with open(card, "w", encoding="utf-8") as fh:
        fh.write(CARD.replace("__LOGO__", build.LOGO).replace("__VER__", build.VERSION))

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        pg.goto("file://" + card, wait_until="networkidle")
        pg.wait_for_timeout(400)
        pg.screenshot(path=os.path.join(ROOT, "assets", "og.png"))
        pg.close()

        # Apple touch icon: the mark on a solid ground, 180x180.
        icon = ('<body style="margin:0;width:180px;height:180px;background:#fff;'
                'display:grid;place-items:center">'
                '<div style="width:118px;height:118px;color:#1a56b8">'
                + build.LOGO.replace('class="mark"', 'style="width:118px;height:118px"')
                + '</div></body>')
        pg = b.new_page(viewport={"width": 180, "height": 180})
        pg.set_content(icon)
        pg.screenshot(path=os.path.join(ROOT, "assets", "icon-180.png"))
        b.close()

    os.remove(card)
    print("wrote assets/og.png and assets/icon-180.png")


if __name__ == "__main__":
    main()
