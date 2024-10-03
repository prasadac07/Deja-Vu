from dotenv import load_dotenv
load_dotenv()  # Load all environment variables

import streamlit as st
import os
import sqlite3
import psycopg2  # For PostgreSQL
import mysql.connector  # For MySQL
from pymongo import MongoClient  # For MongoDB
import google.generativeai as genai

# Configure Genai Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Google Gemini Model and provide queries as response
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text

# Function to connect and query SQLite
def read_sqlite_query(sql, db):
    if not os.path.exists(db):
        st.error(f"Database file does not exist: {db}")
        return []
    
    try:
          # Print the connection string for debugging
        print(f"Connecting to SQLite database: {db}")  # Debugging line

        conn = sqlite3.connect(db)
        cur = conn.cursor()
        print(f"Executing SQL Query: {sql}")  # Debugging line
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        return rows
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return []
    finally:
        conn.close()  # Ensure connection is closed

# Function to connect and query PostgreSQL
def read_postgresql_query(sql, db_params):
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return rows

# Function to connect and query MySQL
def read_mysql_query(sql, db_params):
    conn = mysql.connector.connect(**db_params)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return rows

# Function to query MongoDB
def read_mongodb_query(collection_name, query, db_params):
    client = MongoClient(db_params['host'], db_params['port'])
    db = client[db_params['database']]
    collection = db[collection_name]
    results = collection.find(query)
    return list(results)

# Function to choose database and query
def read_database_query(sql, db_type, db_params):
    if db_type == 'sqlite':
        return read_sqlite_query(sql, db_params['db'])
    elif db_type == 'postgresql':
        return read_postgresql_query(sql, db_params)
    elif db_type == 'mysql':
        return read_mysql_query(sql, db_params)
    elif db_type == 'mongodb':
        collection_name = db_params.get('collection')
        mongo_query = sql_to_mongo_query(sql)  # Convert SQL to MongoDB query
        return read_mongodb_query(collection_name, mongo_query, db_params)
    else:
        return []

# Function to convert SQL to MongoDB query
def sql_to_mongo_query(sql):
    query = {}
    
    if "WHERE" in sql:
        where_clause = sql.split("WHERE")[1].strip()
        conditions = where_clause.split("AND")
        for condition in conditions:
            key, value = condition.split("=")
            key = key.strip()
            value = value.strip().strip('"')  # Remove quotes from around the value
            query[key] = value
    
    return query

# Define your prompt
prompt = [
    """
    You are an expert in converting English questions to SQL query!
    The SQL database has the name STUDENT and has the following columns - NAME, CLASS, 
    SECTION \n\nFor example,\nExample 1 - How many entries of records are present?, 
    the SQL command will be something like this SELECT COUNT(*) FROM STUDENT ;
    \nExample 2 - Tell me all the students studying in Data Science class?, 
    the SQL command will be something like this SELECT * FROM STUDENT 
    where CLASS="Data Science"; 
    also the sql code should not have ``` in beginning or end and sql word in output
    """
]

# Streamlit App configuration
st.set_page_config(page_title="SQL Query Generator and Executor", layout="wide")

# Sidebar: Database Configuration
st.sidebar.header("Database Configuration")

db_type = st.sidebar.selectbox("Select Database Type", ["sqlite", "postgresql", "mysql", "mongodb"])

# Get input for database parameters based on the selection
if db_type == 'sqlite':
    db_path = st.sidebar.text_input("Enter SQLite DB name")
    # Append .db to the path if not present
    if db_path and not db_path.endswith('.db'):
        db_path += '.db'
    db_params = {'db': db_path}
elif db_type == 'postgresql':
    db_params = {
        'host': st.sidebar.text_input("PostgreSQL Host"),
        'port': st.sidebar.number_input("PostgreSQL Port", value=5432),
        'user': st.sidebar.text_input("PostgreSQL User"),
        'password': st.sidebar.text_input("PostgreSQL Password", type="password"),
        'dbname': st.sidebar.text_input("PostgreSQL Database Name"),
    }
elif db_type == 'mysql':
    db_params = {
        'host': st.sidebar.text_input("MySQL Host"),
        'port': st.sidebar.number_input("MySQL Port", value=3306),
        'user': st.sidebar.text_input("MySQL User"),
        'password': st.sidebar.text_input("MySQL Password", type="password"),
        'database': st.sidebar.text_input("MySQL Database Name"),
    }
elif db_type == 'mongodb':
    db_params = {
        'host': st.sidebar.text_input("MongoDB Host"),
        'port': st.sidebar.number_input("MongoDB Port", value=27017),
        'database': st.sidebar.text_input("MongoDB Database Name"),
        'collection': st.sidebar.text_input("MongoDB Collection Name")
    }

# Main section: Query Input and Display Results
st.header("Gemini App To Retrieve SQL Data")

# Get the user's query/question
question = st.text_input("Input your question in natural language:", key="input")

submit = st.button("Ask the question")

# If submit is clicked
if submit:
    # Generate the SQL query using Gemini
    response = get_gemini_response(question, prompt)
    st.write(f"Generated SQL/Query: {response}")

    # Query the database based on the generated SQL
    if db_type == 'mongodb':
        mongo_query = sql_to_mongo_query(response)  # Convert SQL response to MongoDB query
        result = read_database_query(mongo_query, db_type, db_params)
    else:
        result = read_database_query(response, db_type, db_params)
    
    # Display the results
    st.subheader("Query Results")
    if result:
        for row in result:
            st.write(row)
    else:
        st.write("No results found or an error occurred.")
