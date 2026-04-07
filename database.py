"""
Centralized database connection manager.
Loads credentials from .env and provides a shared SQLAlchemy engine.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

DB_HOSTNAME = os.getenv('DB_HOSTNAME')
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')

TABLE_PATIENTS = 'icu_patients'
TABLE_ALERTS = 'icu_alerts'
TABLE_BED_AVAILABILITY = 'icu_bed_availability'
TABLE_NURSE_ASSIGNMENTS = 'icu_nurse_assignments'

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        if None in [DB_HOSTNAME, DB_USERNAME, DB_PASSWORD, DB_PORT, DB_NAME] or \
           'your_' in (DB_HOSTNAME or '') or 'your_' in (DB_USERNAME or ''):
            print("ERROR: Database credentials not configured!")
            print("Please update the .env file with the credentials from Navid.")
            sys.exit(1)
        url = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}"
        _engine = create_engine(url, pool_pre_ping=True, pool_recycle=3600)
        try:
            with _engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[OK] Connected to MySQL database successfully!")
        except Exception as e:
            print(f"DB CONNECTION ERROR: {e}")
            sys.exit(1)
    return _engine
