"""Playwright probe for WISQARS + GVA — capture SPA structure + network calls.

Outputs:
  D:/Gun Violence/_scripts/probe_output/
    wisqars/{page.html, screenshot.png, network_log.json}
    gva/{page.html, screenshot.png, network_log.json}
"""
import pathlib, json, sys
from playwright.sync_api import sync_playwright

OUT = pathlib.Path(r"D:/Gun Violence/_scripts/probe_output")
OUT.mkdir(parents=True, exist_ok=True)

def probe(target_url, label):
    out = OUT / label
    out.mkdir(exist_ok=True)
    print(f"\n=== Probing {label}: {target_url} ===")
    network = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.new_page()
        page.on("request", lambda r: network.append({
            "url": r.url, "method": r.method, "type": r.resource_type,
            "post_data": (r.post_data[:500] if r.post_data else None),
        }))
        page.on("response", lambda r: network.append({
            "type": "response", "url": r.url, "status": r.status,
        }))
        try:
            page.goto(target_url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"  goto error: {e}")
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e2:
                print(f"  fallback goto error: {e2}")

        # Settle
        page.wait_for_timeout(5000)

        # Save artifacts
        (out / "page.html").write_text(page.content(), encoding="utf-8")
        page.screenshot(path=str(out / "screenshot.png"), full_page=True)
        (out / "network_log.json").write_text(json.dumps(network, indent=2)[:2_000_000], encoding="utf-8")
        (out / "title.txt").write_text(page.title(), encoding="utf-8")

        # Try to find data-relevant links / buttons / form actions
        try:
            links = page.eval_on_selector_all("a[href]", "els => els.map(e => ({text: e.innerText.trim(), href: e.href}))")
            (out / "links.json").write_text(json.dumps(links[:200], indent=2), encoding="utf-8")
        except Exception as e:
            (out / "links.json").write_text(f"err: {e}")
        try:
            buttons = page.eval_on_selector_all("button", "els => els.map(e => e.innerText.trim()).filter(t => t.length > 0 && t.length < 100)")
            (out / "buttons.json").write_text(json.dumps(buttons[:100], indent=2), encoding="utf-8")
        except Exception as e:
            (out / "buttons.json").write_text(f"err: {e}")

        browser.close()
        print(f"  wrote {out}")
        # API endpoints summary
        apis = [n for n in network if n.get("type") == "xhr" or n.get("type") == "fetch" or "/api" in n.get("url","")]
        print(f"  XHR/fetch/api hits: {len(apis)}")
        for n in apis[:20]:
            print(f"    [{n.get('method','?')}] {n.get('url','')[:120]}")

probe("https://wisqars.cdc.gov/explore/fatal", "wisqars")
probe("https://www.gunviolencearchive.org/reports", "gva")
print("\nDONE")
