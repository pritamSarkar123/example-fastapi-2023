import time

import psycopg2
from psycopg2.extras import RealDictCursor


def make_db_connection():
    s = 2
    while True:
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="fastapi",
                user="postgres",
                password="root",
                cursor_factory=RealDictCursor,
            )
            cursor = conn.cursor()
            print("Database connection was successful ...")
            return conn, cursor
        except Exception as e:
            print(f"Failed to connect with db for : {e} retrying after {s} seconds ...")
            time.sleep(s)
            s += 2
