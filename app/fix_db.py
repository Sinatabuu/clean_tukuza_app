import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'discipleship_agent.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("DROP TABLE IF EXISTS growth_journal;")
    conn.commit()
    print("Successfully dropped 'growth_journal' table.")
except Exception as e:
    print(f"Error dropping table: {e}")
finally:
    conn.close()