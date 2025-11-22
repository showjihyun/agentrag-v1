"""Check tools in database."""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    database='agenticrag',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

# Check HTTP tools
print("=== HTTP Tools ===")
cur.execute("""
    SELECT id, name, category, implementation_type 
    FROM tools 
    WHERE id LIKE '%http%' OR name LIKE '%HTTP%' OR name LIKE '%http%'
""")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, Category: {row[2]}, Type: {row[3]}")

# Check Python Code tool
print("\n=== Python Code Tool ===")
cur.execute("""
    SELECT id, name, category, implementation_type 
    FROM tools 
    WHERE id LIKE '%python%' OR name LIKE '%Python%'
""")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, Category: {row[2]}, Type: {row[3]}")

# Check all tools
print("\n=== All Tools ===")
cur.execute("SELECT id, name, category FROM tools ORDER BY category, name")
for row in cur.fetchall():
    print(f"{row[2]:15} | {row[0]:20} | {row[1]}")

cur.close()
conn.close()
