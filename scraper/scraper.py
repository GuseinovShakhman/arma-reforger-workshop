"""
scraper.py — Main scraper logic using Playwright headless Chromium.

Usage:
    python scraper/scraper.py          # run continuously via scheduler
    python scraper/scraper.py --once   # run a single scrape pass and exit
"""

from __future__ import annotations
import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta, timezone

from playwright.async_api import async_playwright, Page, Browser

# Allow running as a module or directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.parser import parse_mod_card, parse_mod_detail, extract_mod_id_from_url
from api.database import SessionLocal
from api.models import Mod

WORKSHOP_URL = "https://reforger.armaplatform.com/workshop"
PAGE_DELAY_MS = 2000          # 2s between page loads
DETAIL_DELAY_MS = int(os.getenv("SCRAPE_DETAIL_DELAY_MS", "500"))
DETAIL_SKIP_MINUTES = 10      # skip detail re-fetch if scraped within 10 min

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core scraping functions
# ---------------------------------------------------------------------------

async def scrape_all(browser: Browser) -> None:
    """Scrape all workshop pages and upsert mods into the database."""
    page = await browser.new_page()
    page.set_default_timeout(30_000)

    try:
        mod_summaries = await scrape_listing_pages(page)
        log.info(f"Found {len(mod_summaries)} mods in listing")

        db = SessionLocal()
        try:
            for summary in mod_summaries:
                await upsert_mod_with_detail(page, db, summary)
            db.commit()
            log.info("Scrape complete — database updated")
        finally:
            db.close()
    except Exception as exc:
        log.error(f"Fatal error during scrape: {exc}", exc_info=True)
    finally:
        await page.close()


async def scrape_listing_pages(page: Page) -> list[dict]:
    """Navigate the workshop listing and extract all mod card summaries."""
    summaries: list[dict] = []
    await page.goto(WORKSHOP_URL, wait_until="networkidle")

    while True:
        # Wait for mod cards to render
        try:
            await page.wait_for_selector("[class*='mod-card'], [class*='ModCard'], article", timeout=15_000)
        except Exception:
            log.warning("No mod cards found on page — stopping pagination")
            break

        html = await page.content()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Try various card selectors used by Next.js workshop
        cards = (
            soup.find_all(class_=lambda c: c and ("mod-card" in c.lower() or "modcard" in c.lower()))
            or soup.find_all("article")
        )

        if not cards:
            log.warning("No card elements found — HTML structure may have changed")
            break

        for card in cards:
            try:
                data = parse_mod_card(card)
                if data.get("id"):
                    summaries.append(data)
            except Exception as exc:
                log.warning(f"Failed to parse card: {exc}")

        # Attempt to click "next page" button
        next_btn = await page.query_selector("button[aria-label*='next'], a[aria-label*='next'], [class*='next']")
        if not next_btn:
            break

        is_disabled = await next_btn.get_attribute("disabled")
        if is_disabled is not None:
            break

        await next_btn.click()
        await page.wait_for_timeout(PAGE_DELAY_MS)

    return summaries


async def upsert_mod_with_detail(page: Page, db, summary: dict) -> None:
    """Fetch detail page for a mod (if needed) and upsert into DB."""
    mod_id = summary["id"]

    # Check if we should skip detail fetch
    existing: Mod | None = db.query(Mod).filter(Mod.id == mod_id).first()
    skip_detail = False
    if existing and existing.scraped_at:
        age = datetime.now(timezone.utc) - existing.scraped_at.replace(tzinfo=timezone.utc)
        if age < timedelta(minutes=DETAIL_SKIP_MINUTES):
            skip_detail = True

    detail: dict = {}
    if not skip_detail:
        try:
            detail_url = summary.get("workshop_url") or f"{WORKSHOP_URL}/{mod_id}"
            await page.goto(detail_url, wait_until="networkidle")
            await page.wait_for_timeout(DETAIL_DELAY_MS)
            html = await page.content()
            detail = parse_mod_detail(html)
        except Exception as exc:
            log.warning(f"Failed to fetch detail for mod {mod_id}: {exc}")

    merged = {**summary, **detail, "scraped_at": datetime.utcnow()}

    if existing:
        for key, value in merged.items():
            if value is not None:
                setattr(existing, key, value)
    else:
        db.add(Mod(**{k: v for k, v in merged.items() if hasattr(Mod, k)}))

    try:
        db.flush()
    except Exception as exc:
        log.error(f"DB flush failed for mod {mod_id}: {exc}")
        db.rollback()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def run_once() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            await scrape_all(browser)
        finally:
            await browser.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    asyncio.run(run_once())
