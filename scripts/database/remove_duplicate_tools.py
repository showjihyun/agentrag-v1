"""Remove duplicate Python executor tool."""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    database='agenticrag',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

print("=== Before Removal ===")
cur.execute("""
    SELECT id, name, category, implementation_type 
    FROM tools 
    WHERE id LIKE '%python%'
""")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, Category: {row[2]}, Type: {row[3]}")

# Remove old python_executor
print("\n=== Removing python_executor ===")
cur.execute("DELETE FROM tools WHERE id = 'python_executor'")
conn.commit()
print(f"Deleted {cur.rowcount} row(s)")

print("\n=== After Removal ===")
cur.execute("""
    SELECT id, name, category, implementation_type 
    FROM tools 
    WHERE id LIKE '%python%'
""")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, Category: {row[2]}, Type: {row[3]}")

cur.close()
conn.close()

print("\n✅ Cleanup complete!")
