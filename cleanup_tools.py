"""Cleanup duplicate tools."""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    database='agenticrag',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

print("=== Removing python_executor ===")
cur.execute("DELETE FROM tools WHERE id = %s", ('python_executor',))
conn.commit()
print(f"✅ Deleted {cur.rowcount} row(s)")

print("\n=== Remaining Python Tools ===")
cur.execute("SELECT id, name, category FROM tools WHERE category = 'code'")
for row in cur.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]}")

cur.close()
conn.close()
