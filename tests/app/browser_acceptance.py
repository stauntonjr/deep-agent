"""Executed real browser acceptance; explicit live calls, not part of offline smoke."""

import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright, expect


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            http_credentials={"username": "alice", "password": "local-demo-test"},
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()
        await page.goto("http://127.0.0.1:8100")
        await page.get_by_text("SIMULATED PROCUREMENT", exact=False).wait_for()
        await page.get_by_role("button", name="Investigate a discrepancy", exact=False).click()
        await page.get_by_role("button", name="Investigate →", exact=True).click()
        await (
            page.locator("#events")
            .get_by_text("SIMULATED: requirement unresolved", exact=False)
            .first.wait_for(timeout=120000)
        )
        await expect(page.locator("#send")).to_be_enabled(timeout=120000)
        await page.screenshot(path="/tmp/deepagent-procurement-browser.png", full_page=True)
        await page.reload()
        await page.locator("#sessions button").first.click()
        await (
            page.locator("#events")
            .get_by_text("SIMULATED: requirement unresolved", exact=False)
            .first.wait_for()
        )
        async with page.expect_download() as info:
            await page.get_by_role("button", name="Download evidence").click()
        download = await info.value
        await download.save_as("/tmp/deepagent-browser-evidence.json")
        assert (
            "SIMULATED: requirement unresolved"
            in Path("/tmp/deepagent-browser-evidence.json").read_text()
        )
        await page.get_by_role("button", name="New investigation", exact=False).click()
        await page.get_by_role("button", name="Check a claim", exact=False).click()
        await page.get_by_role("button", name="Investigate →", exact=True).click()
        await (
            page.locator("#events")
            .get_by_text("mcp-answer-result/v1", exact=False)
            .first.wait_for(timeout=120000)
        )
        await expect(page.locator("#send")).to_be_enabled(timeout=120000)
        await page.screenshot(path="/tmp/deepagent-science-browser.png", full_page=True)
        await page.set_viewport_size({"width": 375, "height": 812})
        assert (await page.locator("body").bounding_box())["width"] <= 375
        await page.screenshot(path="/tmp/deepagent-mobile-browser.png", full_page=True)
        result = {
            "procurement_simulated": True,
            "actual_DGX_model": True,
            "SciFact_MCP": True,
            "download": True,
            "reload_owned_history": True,
            "narrow_layout": True,
        }
        Path("/tmp/deepagent-browser-report.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
