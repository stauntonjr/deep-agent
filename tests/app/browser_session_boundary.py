"""Delayed HTTP browser probe; no model or domain service calls."""

import asyncio
import json

from playwright.async_api import async_playwright, expect


async def main():
    started, release = asyncio.Event(), asyncio.Event()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(
            http_credentials={"username": "alice", "password": "local-demo-test"}
        )

        async def route(handler):
            path = handler.request.url.split("8100", 1)[1]
            if path.endswith("/run"):
                assert path == "/api/sessions/A/run"
                started.set()
                await release.wait()
                await handler.fulfill(
                    body=json.dumps({"kind": "answer", "text": "A evidence"}) + "\n",
                    content_type="application/x-ndjson",
                )
            elif path == "/api/sessions":
                await handler.fulfill(json=[{"id": "A"}, {"id": "B"}])
            else:
                sid = path.rsplit("/", 1)[1]
                await handler.fulfill(
                    json={"id": sid, "events": [{"kind": "answer", "text": sid + " history"}]}
                )

        await page.route("**/api/**", route)
        await page.goto("http://127.0.0.1:8100")
        await page.get_by_role("button", name="Investigation · A", exact=True).click()
        await page.get_by_text("A history", exact=True).wait_for()
        await page.get_by_role("button", name="Investigate a discrepancy", exact=False).click()
        await page.locator("#send").click()
        await asyncio.wait_for(started.wait(), 5)
        await expect(
            page.get_by_role("button", name="Investigation · B", exact=True)
        ).to_be_disabled()
        await expect(page.locator("#new")).to_be_disabled()
        release.set()
        await expect(page.locator("#send")).to_be_enabled(timeout=10000)
        await page.get_by_text("A evidence", exact=True).wait_for()
        await page.get_by_role("button", name="Investigation · B", exact=True).click()
        await page.get_by_text("B history", exact=True).wait_for()
        await expect(page.get_by_text("A evidence", exact=True)).to_have_count(0)
        await browser.close()
    print("delayed stream: navigation locked; evidence stays in originating session")


if __name__ == "__main__":
    asyncio.run(main())
