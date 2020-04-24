import argparse
import sys
import logging
import logging.config

import feeds.observer as observer
import feeds.web as web

logging.config.dictConfig({
    "version": 1,
    "handlers": {
        "feeds_handler": {
            "class": "logging.StreamHandler",
            "formatter": "feeds_formatter",
        }
    },
    "loggers": {
        "feeds": {
            "handlers": ["feeds_handler"],
            "level": "DEBUG",
        }
    },
    "formatters": {
        "feeds_formatter": {
            "format": '[%(asctime)s,%(msecs)d] %(funcName)s %(message)s',
            "datefmt": '%H:%M:%S',
        }
    }
})
log = logging.getLogger('feeds')
log.setLevel(logging.DEBUG)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--observer', default=False)
    parser.add_argument('--web', default=False)
    args = parser.parse_args()

    if args.observer:
        sys.exit(observer.run())
    if args.web:
        sys.exit(web.run())

    parser.print_help()
    sys.exit(1)
