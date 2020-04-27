import asyncio
import re
import datetime
import os
import io
import aiohttp
import json
import logging
# from tenacity import retry, stop_after_attempt
import requests
from typing import Tuple, List, Dict
from bs4 import BeautifulSoup
from newspaper import Article, ArticleException

from ..models import models as models
from ..models import cache as cache
from .. import config

log = logging.getLogger('feeds.observer')
log.setLevel(logging.DEBUG)


re_uri = re.compile('http(?:s|)://(?:www\.|)(?P<name>[a-z0-9]+).*')


# @retry(stop=stop_after_attempt(3))
async def process_item(feed: models.Feed) -> Tuple[str, int]:
    async with aiohttp.ClientSession() as session:
        async with session.get(feed.uri) as response:
            status = response.status
            if status == 200:
                data = await response.read()
                if feed.name == 'hn':
                    log.debug(f'Accessing HN API...')
                    await parse_hn_items_from_json(feed, data)
                    # asyncio.wait()
    log.debug(f'Done with {feed}')


def load_page_safe(url):
    try:
        response = requests.get(
            url=url,
            timeout=config.DEFAULT_REQUEST_TIMEOUT,
            headers=config.DEFAULT_REQUEST_HEADERS,
            stream=True  # the most important part — stream response to prevent
                         # loading everything into memory
        )
    except requests.RequestException as e:
        log.warning(f'Error parsing the page: {url} {e}')
        return ''

    html = io.StringIO()
    total_bytes = 0

    for chunk in response.iter_content(chunk_size=100 * 1024, decode_unicode=True):
        total_bytes += len(chunk)
        if total_bytes >= config.MAX_PARSABLE_CONTENT_LENGTH:
            return ""  # reject too big pages
        html.write(str(chunk))

    return html.getvalue()


def parse_article(url) -> Tuple[str, List[str]]:
    """Parse article using newspaper3k to get summary and keywords."""
    if not url:
        return "", []
    article = Article(url)
    html_content = load_page_safe(url)
    if not html_content:
        return "", []
    article.set_html(html_content)
    article.parse()
    article.nlp()
    return article.summary, list(set(article.keywords))


async def parse_hn_items_from_json(feed: models.Feed, data: str):
    """Parse HN using JSON API: https://github.com/HackerNews/API"""
    json_data = json.loads(data)

    async with aiohttp.ClientSession() as session:
        for sid in json_data:
            item_url = f'https://hacker-news.firebaseio.com/v0/item/{sid}.json'
            async with session.get(item_url) as response:
                status = response.status
                if status != 200:
                    continue

                item_data = await response.read()
                json_item = json.loads(item_data)
                if json_item.get('type') != 'story':
                    continue

                # Check post score
                if not json_item.get('score'):
                    continue
                if int(json_item.get('score')) < config.HN_SCORE_THRESHOLD:
                    continue

                # Parse datetime
                ts = json_item.get('time')
                if not ts:
                    continue
                try:
                    dt = datetime.datetime.fromtimestamp(ts)
                except ValueError:
                    continue

                link = json_item.get('url')
                title = json_item.get('title')
                if not title or not link:
                    continue
                if title.startswith('Ask HN:') and not link.startswith('http'):
                    link = f'https://news.ycombinator.com/{link}'

                try:
                    summary, keywords = parse_article(link)
                except ArticleException:
                    summary = ""
                    keywords = []

                new_item = models.create_item(heading=title,
                                              link=link,
                                              text=summary)
                new_item.datetime = dt
                new_item.feed_id = feed.id
                new_item.icon_path = get_feed_icon_path(new_item, 'hn')
                models.save_item(new_item, keywords)

        items = models.get_feed_items(45)
        cache.set_feed_items(items)


def get_feed_icon_path(feed: models.Item, feed_name: str):
    feed_icon: str = ''

    # Set icon based on URL in the feed link
    if feed.link:
        m = re.search(re_uri, feed.link)
        if m:
            site_name = m.groupdict()['name']
            if os.path.exists(f'feeds/web/static/icons/{site_name}.png'):
                feed_icon = f'/static/icons/{site_name}.png'

    # Set icon based on feed source
    if not feed_icon:
        if os.path.exists(f'feeds/web/static/icons/{feed_name}.png'):
            # Check content type
            if feed.heading and feed_name == 'hn' and '[pdf]' in feed.heading:
                feed_icon = f'/static/icons/pdf.png'
            else:
                feed_icon = f'/static/icons/{feed_name}.png'
        else:
            feed_icon = '/static/icons/default.png'

    return feed_icon


async def fetch_sources(sources):
    """Run coroutines that fetch latest data for a given sources."""
    log.debug(f'Fetching: {len(sources)} sources')
    futures = [process_item(src) for src in sources]
    await asyncio.gather(*futures)
