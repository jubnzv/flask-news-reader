import os
import logging
import jinja2
import timeago
import datetime
import dateutil.parser
from typing import Dict
from flask import Flask, render_template, send_from_directory, request

from .. import config
from ..models import models as models
from ..models import cache as cache

log = logging.getLogger('feeds.web')
log.setLevel(logging.WARNING)

app = Flask(__name__)
app.config.from_pyfile('../config.py')

_js_escapes = {
    '\\': '\\u005C',
    '\'': '\\u0027',
    '"': '\\u0022',
    '>': '\\u003E',
    '<': '\\u003C',
    '&': '\\u0026',
    '=': '\\u003D',
    '-': '\\u002D',
    ';': '\\u003B',
    u'\u2028': '\\u2028',
    u'\u2029': '\\u2029'
}

# Escape every ASCII character with a value less than 32
_js_escapes.update(('%c' % z, '\\u%04X' % z) for z in range(32))


@app.template_filter('escapejs')
def jinja2_escapejs_filter(value):
    retval = []
    for letter in value:
        if letter in _js_escapes:
            retval.append(_js_escapes[letter])
        else:
            retval.append(letter)

    return jinja2.Markup("".join(retval))


def format_feed_items(feed_items: Dict):
    """Format serialized feed items to format used in Jinja2 templates."""
    for i, f in enumerate(feed_items):
        if 'datetime' in f:
            # Since Python 3.7:
            # jf['datetime'] = date.fromisoformat(jf['datetime'])
            feed_items[i]['datetime'] = dateutil.parser.parse(f['datetime'])
            feed_items[i]['timeago'] = timeago.format(
                feed_items[i]['datetime'], datetime.datetime.now())


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
def index():
    return render_template('pages/placeholder.index.html',
                           title='index')


@app.route('/feed', methods=['GET'])
def feed():
    tags = request.args.get('tags')
    if tags:
        title = f"feed[{', '.join(tags.split(','))}]"
        feed_items = [i.serialize()
                      for i in models.get_feed_items_with_tags(tags.split(','))]
    else:
        feed_items = cache.get_feed_items(45)
        title = 'feed'
    format_feed_items(feed_items)
    return render_template('pages/placeholder.feed.html',
                           title=title,
                           feed_items=feed_items)


def run():
    app.run(host='0.0.0.0', port=8000)
