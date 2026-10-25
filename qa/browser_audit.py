"""Local browser evidence. Run: uv run --with playwright python qa/browser_audit.py.
Optional authenticated storage state: --storage-state PATH (never commit it).
"""

import argparse
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="qa/evidence")
    parser.add_argument("--storage-state")
    parser.add_argument(
        "--axe-script", help="Optional locally downloaded axe-core script"
    )
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
        )
        context = browser.new_context(
            storage_state=args.storage_state, reduced_motion="reduce"
        )
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(args.base_url, wait_until="networkidle")
        paths = {"/", "/owner/", "/owner/login/"}
        for href in page.locator("a[href]").evaluate_all(
            '(els) => els.map(e => e.getAttribute("href"))'
        ):
            url = urljoin(args.base_url, href)
            if urlsplit(url).netloc == urlsplit(args.base_url).netloc:
                path = urlsplit(url).path
                if not path.startswith(("/media/", "/static/")):
                    paths.add(path)
        # Include detail and category links from the full catalogue, not only featured products.
        if "/products/" in paths:
            page.goto(args.base_url + "/products/", wait_until="networkidle")
            for href in page.locator("a[href]").evaluate_all(
                '(els) => els.map(e => e.getAttribute("href"))'
            ):
                if href.startswith(("/products/", "/categories/")):
                    paths.add(urlsplit(href).path)
        for width in (360, 768, 1440):
            page.set_viewport_size({"width": width, "height": 1000})
            for index, path in enumerate(sorted(paths)):
                errors.clear()
                response = page.goto(args.base_url + path, wait_until="networkidle")
                # Full-page captures do not necessarily load below-the-fold lazy images.
                # Request and decode them before deciding whether any image is broken.
                page.evaluate("""async () => {
                    const images = [...document.images];
                    images.forEach(image => { image.loading = 'eager'; });
                    await Promise.all(images.map(image => image.decode().catch(() => null)));
                }""")
                page.screenshot(
                    path=str(output / f"{width}-{index:02d}.png"), full_page=True
                )
                result = page.evaluate("""() => ({
                    title: document.title,
                    h1: [...document.querySelectorAll('h1')].map(e => e.textContent.trim()),
                    overflow: document.documentElement.scrollWidth > innerWidth,
                    brokenImages: [...document.images].filter(e => !e.complete || e.naturalWidth === 0).map(e => e.src),
                    missingAlts: [...document.images].filter(e => !e.hasAttribute('alt')).length,
                    canonical: document.querySelector('link[rel="canonical"]')?.href,
                    description: document.querySelector('meta[name="description"]')?.content,
                    robots: document.querySelector('meta[name="robots"]')?.content,
                    jsonld: [...document.querySelectorAll('script[type="application/ld+json"]')].map(e => {try { return JSON.parse(e.textContent) } catch { return {error:'Invalid JSON'} } }),
                    timing: performance.getEntriesByType('navigation').map(e => ({domContentLoaded:e.domContentLoadedEventEnd,load:e.loadEventEnd,bytes:e.transferSize}))
                })""")
                page.keyboard.press("Tab")
                result.update(
                    path=path,
                    final_url=page.url,
                    width=width,
                    status=response.status,
                    screenshot=f"{width}-{index:02d}.png",
                    errors=list(errors),
                    keyboard_focus=page.evaluate(
                        "document.activeElement.outerHTML.slice(0,400)"
                    ),
                )
                if args.axe_script:
                    page.add_script_tag(path=args.axe_script)
                    audit = page.evaluate(
                        "async () => await axe.run(document, {runOnly:{type:'tag', values:['wcag2a','wcag2aa','wcag21aa']}})"
                    )
                    result["accessibility_violations"] = audit["violations"]
                results.append(result)
                (output / "results.json").write_text(json.dumps(results, indent=2))
        # Progressive enhancement smoke test, using a real browser without JavaScript.
        no_js = browser.new_context(
            java_script_enabled=False, viewport={"width": 360, "height": 900}
        )
        plain = no_js.new_page()
        for path in ("/", "/products/"):
            response = plain.goto(args.base_url + path)
            assert response.status == 200, (path, response.status)
            assert plain.locator("h1").count() == 1, path
        no_js.close()
        browser.close()
    problems = [
        r
        for r in results
        if r["status"] >= 400
        or r["overflow"]
        or r["brokenImages"]
        or r["errors"]
        or r["missingAlts"]
        or r.get("accessibility_violations")
    ]
    print(
        json.dumps(
            {
                "pages_and_viewports": len(results),
                "problems": problems,
                "output": str(output.resolve()),
            },
            indent=2,
        )
    )
    raise SystemExit(bool(problems))


if __name__ == "__main__":
    main()
