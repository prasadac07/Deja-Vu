import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect('sqllite_1.db')

# Create a cursor object
cur = conn.cursor()

# Drop the existing STUDENT table if it exists
cur.execute("DROP TABLE IF EXISTS STUDENT;")

# SQL command to create the STUDENT table with an additional MARKS column
create_table_student = """
CREATE TABLE STUDENT (
    NAME TEXT,
    CLASS TEXT,
    SECTION TEXT,
    MARKS INTEGER
);
"""

# Execute the query to create the STUDENT table
cur.execute(create_table_student)

# Insert some example data into the STUDENT table
students_data = [
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

# Insert the new data into the STUDENT table
cur.executemany("INSERT INTO STUDENT (NAME, CLASS, SECTION, MARKS) VALUES (?, ?, ?, ?)", students_data)

# Drop the existing WORKER table if it exists
cur.execute("DROP TABLE IF EXISTS WORKER;")

# SQL command to create the WORKER table with additional columns for job role and salary
create_table_worker = """
CREATE TABLE WORKER (
    NAME TEXT,
    DEPARTMENT TEXT,
    ROLE TEXT,
    SALARY INTEGER
);
"""

# Execute the query to create the WORKER table
cur.execute(create_table_worker)

# Insert some example data into the WORKER table
workers_data = [
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

# Insert the new data into the WORKER table
cur.executemany("INSERT INTO WORKER (NAME, DEPARTMENT, ROLE, SALARY) VALUES (?, ?, ?, ?)", workers_data)

# Commit changes and close the connection
conn.commit()
conn.close()

print("STUDENT and WORKER tables created and sample data inserted successfully.")