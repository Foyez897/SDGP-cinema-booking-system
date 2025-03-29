import sqlite3
import os

# Path to DB and output file
db_path = 'database/horizon_cinemas.db'
output_path = 'database/all_data.txt'

# Connect to the database
conn = sqlite3.connect(db_path)

# Export all tables and their contents
with open(output_path, 'w') as f:
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table_name in tables:
        table = table_name[0]

        f.write(f"\n\n-- Table: {table}\n\n")

        # Table schema
        f.write(f"-- Schema:\n")
        cursor.execute(f"PRAGMA table_info({table})")
        schema_info = cursor.fetchall()
        for col in schema_info:
            f.write(f"{col[1]} ({col[2]})\n")

        # Table content
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        columns = [col[1] for col in schema_info]

        f.write('\n' + '\t'.join(columns) + '\n')
        f.write('-' * 50 + '\n')
        for row in rows:
            f.write('\t'.join(str(item) for item in row) + '\n')

# Close connection
conn.close()
print("✅ All data and schema exported to 'database/all_data.txt' successfully!");