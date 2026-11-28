from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("RAG_DB_NAME"),
    user=os.getenv("RAG_DB_USER"),
    password=os.getenv("RAG_DB_PASSWORD"),
    host=os.getenv("RAG_DB_HOST"),
    port=os.getenv("RAG_DB_PORT")
)

cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM chunks")
print("Total chunks:", cur.fetchone()[0])

cur.execute(
    "SELECT COUNT(*) FROM chunks WHERE content LIKE %s",
    ("%TEMPORARY%",)
)
print("Temporary test records:", cur.fetchone()[0])

cur.close()
conn.close()
