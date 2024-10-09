import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect('./sqllite_1.db')

# Create a cursor object
cur = conn.cursor()

# Drop the existing STUDENTS table if it exists
cur.execute("DROP TABLE IF EXISTS STUDENTS;")

# SQL command to create the STUDENTS table with an additional MARKS column
create_table_STUDENTS = """
CREATE TABLE STUDENTS (
    NAME TEXT,
    CLASS TEXT,
    SECTION TEXT,
    MARKS INTEGER
);
"""

# Execute the query to create the STUDENTS table
cur.execute(create_table_STUDENTS)

# Insert some example data into the STUDENTS table
STUDENTS_data = [
    ('Alice', 'Data Science', 'A', 85),
    ('Bob', 'AI', 'B', 90),
    ('Charlie', 'Cyber Security', 'C', 78),
    ('David', 'Data Science', 'A', 88),
    ('Eva', 'AI', 'B', 92),
    ('Frank', 'Cyber Security', 'C', 80),
    ('Grace', 'Data Science', 'A', 87),
    ('Helen', 'AI', 'B', 95),
    ('Ian', 'Cyber Security', 'C', 82),
    ('Jack', 'Data Science', 'A', 91),
    ('Karen', 'AI', 'B', 89),
    ('Liam', 'Cyber Security', 'C', 77),
    ('Mia', 'Data Science', 'A', 93)
]

# Insert the new data into the STUDENTS table
cur.executemany("INSERT INTO STUDENTS (NAME, CLASS, SECTION, MARKS) VALUES (?, ?, ?, ?)", STUDENTS_data)

# Drop the existing WORKERS table if it exists
cur.execute("DROP TABLE IF EXISTS WORKERS;")

# SQL command to create the WORKERS table with additional columns for job role and salary
create_table_WORKERS = """
CREATE TABLE WORKERS (
    NAME TEXT,
    DEPARTMENT TEXT,
    ROLE TEXT,
    SALARY INTEGER
);
"""

# Execute the query to create the WORKERS table
cur.execute(create_table_WORKERS)

# Insert some example data into the WORKERS table
WORKERS_data = [
    ('John', 'HR', 'Manager', 75000),
    ('Sarah', 'Finance', 'Analyst', 68000),
    ('Tom', 'IT', 'Developer', 82000),
    ('Emma', 'Operations', 'Supervisor', 70000),
    ('Chris', 'Marketing', 'Coordinator', 65000),
    ('Olivia', 'Finance', 'Accountant', 72000),
    ('Liam', 'IT', 'System Admin', 78000),
    ('Sophia', 'HR', 'Recruiter', 64000),
    ('Noah', 'Operations', 'Logistics Manager', 73000),
    ('Ava', 'Marketing', 'Content Specialist', 69000)
]

# Insert the new data into the WORKERS table
cur.executemany("INSERT INTO WORKERS (NAME, DEPARTMENT, ROLE, SALARY) VALUES (?, ?, ?, ?)", WORKERS_data)

# Commit changes and close the connection
conn.commit()
conn.close()

print("STUDENTS and WORKERS tables created and sample data inserted successfully.")