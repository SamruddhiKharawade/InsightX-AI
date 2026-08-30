"""
Creates a SQLAlchemy engine for connecting to PostgreSQL, using credentials
loaded from the .env file. No other script should hardcode DB credentials —
they all import get_engine() from here instead.
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine

# Reads the .env file in the project root and loads its values as
# environment variables, accessible via os.getenv()
load_dotenv()


def get_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
    return create_engine(connection_string)