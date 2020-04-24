import redis
import json
import logging
from typing import List

from .. import config
from . import models

log = logging.getLogger('feeds.models')
log.setLevel(logging.WARNING)


redis = redis.StrictRedis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    decode_responses=True)


def set_feed_items(items: List[models.Item]):
    redis.delete('feed_items')
    for i in items:
        redis.lpush('feed_items', json.dumps(i.serialize()))


def get_feed_items(max_items: int):
    # TODO: How about reversed order?
    feed_items = redis.lrange('feed_items', 0, -1)
    try:
        return list(reversed([json.loads(ji) for ji in feed_items]))
    except json.JSONDecodeError as e:
        log.error(f'Error processing cache data: {str(e)}!')
        return []
