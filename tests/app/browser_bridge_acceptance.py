"""Opt-in real DGX/browser/A2A acceptance; uses existing domain and MCP services."""

import asyncio
import hashlib
import json
import time
from pathlib import Path

from playwright.async_api import async_playwright, expect


async def main():
    started = time.monotonic()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            http_credentials={"username": "alice", "password": "local-demo-test"},
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()
        await page.goto("http://127.0.0.1:8100")
        await page.get_by_role("button", name="Investigate a discrepancy", exact=False).click()
        await page.locator("#send").click()
        await (
            page.locator("#events")
            .get_by_text("Admitted synthetic procurement corpus", exact=False)
            .first.wait_for(timeout=310000)
        )
        await expect(page.locator("#send")).to_be_enabled(timeout=310000)
        await page.screenshot(path="/tmp/deepagent-real-a2a-browser.png", full_page=True)
        async with page.expect_download() as download_info:
            await page.get_by_role("button", name="Download evidence").click()
        await (await download_info.value).save_as("/tmp/deepagent-real-a2a-download.json")
        exported = json.loads(Path("/tmp/deepagent-real-a2a-download.json").read_text())
        tasks = [event["task"] for event in exported["events"] if event["kind"] == "task"]
        assert tasks and tasks[-1]["state"] == "completed" and not tasks[-1]["simulated"]
        evidence = json.loads(tasks[-1]["artifacts"][0]["text"])
        assert evidence["project"] == "atlas" and evidence["item"] == "GPU-A"
        assert evidence["investigation"]["required_quantity"] == "8"
        assert evidence["investigation"]["ordered_quantity"] == "6"
        assert len(evidence["sources"]) == 12
        assert any(
            event["kind"] == "tool" and event["text"] == "investigate_procurement"
            for event in exported["events"]
        )
        assert any(event["kind"] == "answer" for event in exported["events"])
        await page.reload()
        await page.locator("#sessions button").first.click()
        await (
            page.locator("#events")
            .get_by_text("Admitted synthetic procurement corpus", exact=False)
            .first.wait_for()
        )
        bob = await browser.new_context(
            http_credentials={"username": "bob", "password": "local-demo-test"}
        )
        assert (
            await bob.request.get("http://127.0.0.1:8100/api/sessions/" + exported["id"])
        ).status == 404
        assert (
            await bob.request.get(
                "http://127.0.0.1:8100/api/sessions/" + exported["id"] + "/download"
            )
        ).status == 404
        assert (
            await bob.request.get("http://127.0.0.1:8100/api/tasks/" + tasks[-1]["id"])
        ).status == 404
        await page.get_by_role("button", name="New investigation", exact=False).click()
        await page.get_by_role("button", name="Check a claim", exact=False).click()
        await page.locator("#send").click()
        await (
            page.locator("#events")
            .get_by_text("mcp-answer-result/v1", exact=False)
            .first.wait_for(timeout=310000)
        )
        await expect(page.locator("#send")).to_be_enabled(timeout=310000)
        await page.screenshot(path="/tmp/deepagent-real-science-browser.png", full_page=True)
        await page.set_viewport_size({"width": 375, "height": 812})
        assert (await page.locator("body").bounding_box())["width"] <= 375
        await page.screenshot(path="/tmp/deepagent-real-mobile-browser.png", full_page=True)
        result = {
            "actual_DGX_model": True,
            "actual_procurement_A2A": True,
            "synthetic_corpus": True,
            "GPU_A_required": "8",
            "GPU_A_ordered": "6",
            "source_records": 12,
            "owned_reload_download": True,
            "cross_viewer_404": True,
            "SciFact_MCP": True,
            "narrow_layout": True,
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "download_sha256": hashlib.sha256(
                Path("/tmp/deepagent-real-a2a-download.json").read_bytes()
            ).hexdigest(),
        }
        Path("/tmp/deepagent-real-browser-results.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
