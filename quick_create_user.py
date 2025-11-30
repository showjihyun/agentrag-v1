"""Quick create user via SQL"""
import psycopg2
import bcrypt

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="agenticrag",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()

# Hash password
password = "test123"
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Insert user
try:
    cur.execute("""
        INSERT INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at)
        VALUES (gen_random_uuid(), 'testuser', 'test@example.com', %s, 'admin', true, NOW(), NOW())
        ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
        RETURNING id, email
    """, (password_hash,))
    
    result = cur.fetchone()
    conn.commit()
    
    print(f"✅ User created/updated:")
    print(f"   ID: {result[0]}")
    print(f"   Email: {result[1]}")
    print(f"   Password: {password}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
