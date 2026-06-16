import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
cur = conn.cursor()
sql_path = os.path.join(os.path.dirname(__file__), "001_create_tables_postgres.sql")
with open(sql_path, "r") as f:
    cur.execute(f.read())
conn.commit()
print("Migrasi berhasil dijalankan ke Supabase.")
cur.close()
conn.close()
