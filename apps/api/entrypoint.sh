#!/bin/sh
set -e

echo "Waiting for database to be ready..."
python -c "
import time, psycopg, os
db_url = os.environ.get('DATABASE_URL', '')
clean_url = db_url.replace('postgresql+psycopg://', 'postgresql://')
for i in range(30):
    try:
        conn = psycopg.connect(clean_url, connect_timeout=3)
        conn.close()
        print('Database connection established.')
        break
    except Exception as e:
        print(f'Waiting for database... ({i+1}/30)')
        time.sleep(1)
"

echo "Applying database migrations..."
alembic upgrade head

echo "Applying retail catalog seed data..."
python -m omnimission.seed.loader || true

echo "Starting OmniMission API on 0.0.0.0:8000..."
exec uvicorn omnimission.main:app --host 0.0.0.0 --port 8000
