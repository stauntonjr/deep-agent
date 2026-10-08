"""Opt-in real DGX/browser/A2A acceptance; uses existing domain and MCP services."""

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path

from playwright.async_api import async_playwright, expect


async def main():
    started = time.monotonic()
    base_url = os.getenv("DEEPAGENT_BROWSER_URL", "http://127.0.0.1:8100")
    prefix = os.getenv("DEEPAGENT_BROWSER_PREFIX", "/tmp/deepagent-real")
    credentials = (
        json.loads(Path(os.environ["DEEPAGENT_BROWSER_CREDENTIALS"]).read_text())
        if os.getenv("DEEPAGENT_BROWSER_CREDENTIALS")
        else {name: {"username": name, "password": "local-demo-test"} for name in ("alice", "bob")}
    )
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            http_credentials=credentials["alice"],
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()
        await page.goto(base_url)
        await page.get_by_role("button", name="Investigate a discrepancy", exact=False).click()
        await page.locator("#send").click()
        await (
            page.locator("#events")
            .get_by_text("Admitted synthetic procurement corpus", exact=False)
            .first.wait_for(timeout=310000)
        )
        await expect(page.locator("#send")).to_be_enabled(timeout=310000)
        await page.screenshot(path=prefix + "-a2a-browser.png", full_page=True)
        async with page.expect_download() as download_info:
            await page.get_by_role("button", name="Download evidence").click()
        await (await download_info.value).save_as(prefix + "-a2a-download.json")
        exported = json.loads(Path(prefix + "-a2a-download.json").read_text())
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
        exchange = [event for event in exported["events"] if event["kind"] == "a2a"]
        assert [event["phase"] for event in exchange] == ["request", "response"]
        assert exchange[0]["correlation_id"] == exchange[1]["correlation_id"]
        assert exchange[1]["observations"]["source_count"] == 12
        assert exchange[1]["elapsed_ms"] > 0
        assert await page.locator(".facts").count() == 1
        assert await page.locator(".task details[open]").count() == 0
        assert await page.locator(".error").count() == 0
        async with page.expect_download() as trace_info:
            await page.get_by_role("button", name="Download trace").click()
        await (await trace_info.value).save_as(prefix + "-trace.json")
        local_trace = json.loads(Path(prefix + "-trace.json").read_text())
        assert local_trace["session_id"] == exported["id"]
        assert local_trace["events"] == exported["events"]
        await page.reload()
        await page.locator("#sessions button").first.click()
        await (
            page.locator("#events")
            .get_by_text("Admitted synthetic procurement corpus", exact=False)
            .first.wait_for()
        )
        bob = await browser.new_context(http_credentials=credentials["bob"])
        assert (await bob.request.get(base_url + "/api/sessions/" + exported["id"])).status == 404
        assert (
            await bob.request.get(base_url + "/api/sessions/" + exported["id"] + "/download")
        ).status == 404
        assert (await bob.request.get(base_url + "/api/tasks/" + tasks[-1]["id"])).status == 404
        assert (
            await bob.request.get(base_url + "/api/sessions/" + exported["id"] + "/trace")
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
        await page.screenshot(path=prefix + "-science-browser.png", full_page=True)
        await page.set_viewport_size({"width": 375, "height": 812})
        assert (await page.locator("body").bounding_box())["width"] <= 375
        await page.screenshot(path=prefix + "-mobile-browser.png", full_page=True)
        result = {
            "actual_DGX_model": True,
            "actual_procurement_A2A": True,
            "synthetic_corpus": True,
            "GPU_A_required": "8",
            "GPU_A_ordered": "6",
            "source_records": 12,
            "observed_A2A_exchange": True,
            "viewer_owned_trace_download": True,
            "owned_reload_download": True,
            "cross_viewer_404": True,
            "SciFact_MCP": True,
            "narrow_layout": True,
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "download_sha256": hashlib.sha256(
                Path(prefix + "-a2a-download.json").read_bytes()
            ).hexdigest(),
        }
        Path(prefix + "-browser-results.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
