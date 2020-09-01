import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from feeds.config import (PG_USER, PG_PASS, PG_URI, FORCE_INIT_NEW)

def install_ntlk():
    import nltk
    nltk.download('punkt')
    print('NLTK downloaded.')


def initialize_database():
    from sqlalchemy import create_engine
    from sqlalchemy_utils import (database_exists,
                                  create_database,
                                  drop_database)
    engine = create_engine(f'postgresql://{PG_USER}:{PG_PASS}@{PG_URI}/feeds')
    if not database_exists(engine.url):
        create_database(engine.url)
    elif FORCE_INIT_NEW:
        drop_database(engine.url)
        create_database(engine.url)
    else:
        return

    print(f'Database created: {database_exists(engine.url)}')
    for table_name in ['feeds', 'items', 'tags', 'alembic_version']:
        sql = f'DROP TABLE IF EXISTS {table_name} CASCADE;'
        result = engine.execute(sql)
        print(f'Drop table {table_name}: result={result}')


if __name__ == '__main__':
    install_ntlk()
    initialize_database()
