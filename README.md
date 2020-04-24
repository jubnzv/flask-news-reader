# idie.ru

Personal website with a simple web news scrapper.

* [Traefik](https://traefik.io) reverse proxy;
* Flask web application deployed with nginx and uWSGI using [uwsgi-nginx-flask-docker](https://github.com/tiangolo/uwsgi-nginx-flask-docker) container;
* Auxiliary [script](./feeds/observer) that parses news sites and performs scrapping and text analysis;
* Postgres and redis for data storage.

## Setup

### Development
```bash
virtualenv venv --python=/usr/bin/python3 && source venv/bin/activate
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt

docker-compose up -d postgres redis
DEBUG=1 PG_URI=localhost REDIS_HOST=localhost py3 main.py --observer=1
DEBUG=1 PG_URI=localhost REDIS_HOST=localhost py3 main.py --web=1
```

### Production
```bash
sudo deploy/mkswap.sh  # required for low-ram host
docker network create idie_external_network
docker-compose build
POSTGRES_USER='xxx' POSTGRES_PASSWORD='xxx' docker-compose up -d
```
