import os


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://ledger:ledger@localhost:5432/ledger",
)
