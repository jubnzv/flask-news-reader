import hashlib
from datetime import datetime
import sqlalchemy as db
import logging
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import List

from ..config import (PG_USER, PG_PASS, PG_URI)

log = logging.getLogger('feeds.models')
log.setLevel(logging.ERROR)

engine = create_engine(f'postgresql://{PG_USER}:{PG_PASS}@{PG_URI}/feeds')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def _unique(session, cls, hashfunc, queryfunc, constructor, arg, kw):
    cache = getattr(session, '_unique_cache', None)
    if cache is None:
        session._unique_cache = cache = {}

    key = (cls, hashfunc(*arg, **kw))
    if key in cache:
        return cache[key]
    else:
        with session.no_autoflush:
            q = session.query(cls)
            q = queryfunc(q, *arg, **kw)
            obj = q.first()
            if not obj:
                obj = constructor(*arg, **kw)
                session.add(obj)
        cache[key] = obj
        return obj


class UniqueMixin:
    """
    An implementation of Unique Object pattern. See:
    https://github.com/sqlalchemy/sqlalchemy/wiki/UniqueObject#explicit-classmethod-and-session
    """
    @classmethod
    def unique_hash(cls, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, session, *arg, **kw):
        return _unique(
            session,
            cls,
            cls.unique_hash,
            cls.unique_filter,
            cls,
            arg, kw
        )


class Feed(Base):
    """Feed sources: news site."""
    __tablename__ = 'feeds'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    uri = db.Column(db.String(200))
    xpath = db.Column(db.String(500))

    # One to many with items
    items = relationship("Item", backref="feed_ref")

    def __str__(self):
        return f'Feed(name={self.name} uri={self.uri})'


class Item(UniqueMixin, Base):
    """Fetched news item."""
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    heading = db.Column(db.String(512))
    link = db.Column(db.String(512))
    icon_path = db.Column(db.String(512))
    datetime = db.Column(db.DateTime())
    hash = db.Column(db.String(512), unique=True)

    # Reference to feed
    feed_id = db.Column(db.Integer, db.ForeignKey(
        'feeds.id', ondelete='CASCADE'))
    feed = relationship('Feed', back_populates='items')

    # One to many with tags
    tags = relationship("ItemTag", backref="item_ref")

    def __init__(self, text: str, heading="", link=""):
        self.text = text
        self.heading = heading
        self.link = link
        self.hash = Item.unique_hash(text, heading, link)

    @classmethod
    def unique_hash(cls, text, heading, link):
        return f'{link}{heading}{hashlib.sha1(text.encode()).hexdigest()}'

    @classmethod
    def unique_filter(cls, query, text, heading, link):
        return query.filter(Item.text == text,
                            Item.heading == heading,
                            Item.link == link)

    def serialize(self):
        return {
            'text': self.text,
            'heading': self.heading,
            'link': self.link,
            'icon_path': self.icon_path,
            'datetime': datetime.isoformat(self.datetime),
            'tags': [t.serialize() for t in self.tags],
        }


class ItemTag(Base):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)

    # Reference to item
    item_id = db.Column(db.Integer, db.ForeignKey(
        'items.id', ondelete='CASCADE'))
    # item = relationship('Item', back_populates='tags')

    def serialize(self):
        return self.text


def get_feed_sources() -> List[Feed]:
    """Returns list of available feed sources."""
    return Feed.query.all()


def get_feed_items_from_date(max_items: int = 15, from_date: datetime = None):
    """Return up to ``max_items`` of latest feed items starting from
    ``from_date``."""
    # Start of this day
    if not from_date:
        today = datetime.utcnow().date()
        from_date = datetime(today.year, today.month, today.day)
    return get_feed_items(max_items)


def get_feed_items(max_items: int = 15):
    items = Item.query.order_by(desc(Item.datetime)).limit(max_items).all()
    return items


def get_feed_items_with_tags(tag_values: List[str], max_items: int = 100):
    items = Item.query.join(ItemTag, Item.tags)\
        .filter(ItemTag.text.in_(tag_values))\
        .group_by(Item.link,Item.id)\
        .order_by(desc(Item.datetime))\
        .limit(max_items)\
        .all()
    return items


def set_default_feed_sources():
    """Set default values for feed sources (mostly for testing purposes)."""
    f1 = Feed(
        name="hn", uri='https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty')
    # f1 = Feed(name="hn", uri='https://news.ycombinator.com/newest')
    # f2 = Feed(name="habr", uri='https://habr.com/ru/top/')
    db_session.add_all([f1])
    db_session.commit()


def save_item(item: Item, tags: List[str] = []):
    """Save parsed items with related keywords into database."""
    if tags:
        log.debug(f'Item={item.link}: start tags={[t.text for t in item.tags]}')
        item.tags = []
        for i, t in enumerate(tags):
            log.debug(f'Adding tag={t} ({i}/{len(tags)})...')
            it = ItemTag(text=t)
            it.item = item
            it = db_session.merge(it)
            # db_session.add(it)
            item.tags.append(it)
        log.debug(f'Item {item.link}: done tags={[t.text for t in item.tags]}')
    db_session.commit()


def create_item(text="", heading="", link="") -> Item:
    """Create a new Item in compliance with unique constaints."""
    item = Item.as_unique(db_session, text=text, heading=heading, link=link)
    return item

########
# Base.metadata.create_all(engine)
