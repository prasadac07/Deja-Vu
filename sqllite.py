import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect('sqllite_1.db')

# Create a cursor object
cur = conn.cursor()

# Drop the existing STUDENT table if it exists
cur.execute("DROP TABLE IF EXISTS STUDENT;")

# SQL command to create the STUDENT table with an additional MARKS column
create_table_query = """
CREATE TABLE STUDENT (
    NAME TEXT,
    CLASS TEXT,
    SECTION TEXT,
    MARKS INTEGER
);
"""

# Execute the query to create the table
cur.execute(create_table_query)

# Commit changes
conn.commit()

# Insert some example data
cur.execute("INSERT INTO STUDENT (NAME, CLASS, SECTION, MARKS) VALUES ('Alice', 'Data Science', 'A', 85)")
cur.execute("INSERT INTO STUDENT (NAME, CLASS, SECTION, MARKS) VALUES ('Bob', 'AI', 'B', 90)")
cur.execute("INSERT INTO STUDENT (NAME, CLASS, SECTION, MARKS) VALUES ('Charlie', 'Cyber Security', 'C', 78)")

# Commit changes and close the connection
conn.commit()
conn.close()

print("STUDENT table created and sample data inserted successfully.")