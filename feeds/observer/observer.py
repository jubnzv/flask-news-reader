import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..models import get_feed_sources, set_default_feed_sources
from .worker import fetch_sources
from ..config import DEBUG


def launcher():
    """Fetch all available feed sources."""
    # Apply default values at the first launch
    while True:
        sources = get_feed_sources()
        if sources:
            break
        set_default_feed_sources()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(fetch_sources(sources))


def run():
    if DEBUG:
        duration = dict(hour='*', minute='*/1')
    else:
        duration = dict(hour='*/1')

    try:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(launcher, 'cron',
                          next_run_time=datetime.now(),
                          year='*', month='*', day='*', week='*', day_of_week='*',
                          **duration)
    except ValueError:
        scheduler = AsyncIOScheduler(timezone="UTC")
        scheduler.add_job(launcher, 'cron',
                          year='*', month='*', day='*', week='*', day_of_week='*',
                          next_run_time=datetime.now(), **duration)
    scheduler.start()
    print('Press Ctrl+C to exit')

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass

    # loop.close()
