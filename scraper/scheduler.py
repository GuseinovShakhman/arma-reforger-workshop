"""
scheduler.py — APScheduler loop that runs the scraper every N seconds.

Start with:
    python scraper/scheduler.py
"""

from __future__ import annotations
import asyncio
import logging
import os
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.scraper import run_once

log = logging.getLogger(__name__)

SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL_SECONDS", "60"))


def scrape_job() -> None:
    """Synchronous wrapper around the async scraper — called by APScheduler."""
    log.info("Scrape job starting…")
    try:
        asyncio.run(run_once())
    except Exception as exc:
        # NEVER crash the scheduler loop
        log.error(f"Scrape job failed: {exc}", exc_info=True)
    log.info("Scrape job finished")


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        scrape_job,
        trigger=IntervalTrigger(seconds=SCRAPE_INTERVAL),
        id="workshop_scraper",
        name="Arma Reforger Workshop Scraper",
        replace_existing=True,
        max_instances=1,       # never run two scrapes concurrently
        misfire_grace_time=30,
    )

    log.info(f"Scheduler starting — scrape every {SCRAPE_INTERVAL}s")
    # Run immediately on startup, then on schedule
    scrape_job()
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped")


if __name__ == "__main__":
    main()
