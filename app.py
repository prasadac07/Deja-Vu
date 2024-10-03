import streamlit as st
import os
import sqlite3
import psycopg2  # For PostgreSQL
import mysql.connector  # For MySQL
from pymongo import MongoClient  # For MongoDB
import pandas as pd  # For data manipulation
import plotly.express as px  # For data visualization
import google.generativeai as genai

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

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
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(db)
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return pd.DataFrame()

# Function to connect and query PostgreSQL
def read_postgresql_query(sql, db_params):
    try:
        conn = psycopg2.connect(**db_params)
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"PostgreSQL error: {e}")
        return pd.DataFrame()

# Function to connect and query MySQL
def read_mysql_query(sql, db_params):
    try:
        conn = mysql.connector.connect(**db_params)
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"MySQL error: {e}")
        return pd.DataFrame()

# Function to query MongoDB
def read_mongodb_query(collection_name, query, db_params):
    client = MongoClient(db_params['host'], db_params['port'])
    db = client[db_params['database']]
    collection = db[collection_name]
    results = list(collection.find(query))
    return pd.DataFrame(results)

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
        mongo_query = sql_to_mongo_query(sql)
        return read_mongodb_query(collection_name, mongo_query, db_params)
    else:
        return pd.DataFrame()

# Function to convert SQL to MongoDB query
def sql_to_mongo_query(sql):
    query = {}
    if "WHERE" in sql:
        where_clause = sql.split("WHERE")[1].strip()
        conditions = where_clause.split("AND")
        for condition in conditions:
            key, value = condition.split("=")
            key = key.strip()
            value = value.strip().strip('"')
            query[key] = value
    return query

# Define your prompt
prompt = [
    """
    You are an expert in converting English questions to SQL query!
    The SQL database has the name STUDENT and has the following columns - rollno,full_name
    marks,grade,city \n\nFor example,\nExample 1 - How many entries of records are present?, 
    the SQL command will be something like this SELECT COUNT(*) FROM STUDENT ;
    \nExample 2 - Tell me all the students studying in A grade ?, 
    the SQL command will be something like this SELECT * FROM STUDENT 
    where grade="A"; 
    also the sql code should not have ``` in beginning or end and sql word in output
    """
]

# Streamlit App configuration
st.set_page_config(page_title="SQL Query Generator and Executor with Visualization", layout="wide")

# Sidebar: Database Configuration
st.sidebar.header("Database Configuration")

db_type = st.sidebar.selectbox("Select Database Type", ["sqlite", "postgresql", "mysql", "mongodb"])

# Get input for database parameters based on the selection
if db_type == 'sqlite':
    db_path = st.sidebar.text_input("Enter SQLite DB name")
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
st.header("Gemini App To Retrieve and Visualize SQL Data")

# Get the user's question
question = st.text_input("Input your question in natural language:", key="input")

# Function to visualize data using Plotly
def visualize_data(df, chart_type):
    numerical_columns = df.select_dtypes(include='number').columns
    categorical_columns = df.select_dtypes(exclude='number').columns

    if len(categorical_columns) == 0 or len(numerical_columns) == 0:
        st.error("No appropriate data for plotting.")
        return

    if chart_type == "line":
        st.plotly_chart(px.line(df, x=categorical_columns[0], y=numerical_columns[0], title="Line Chart"))
    elif chart_type == "bar":
        st.plotly_chart(px.bar(df, x=categorical_columns[0], y=numerical_columns[0], title="Bar Chart"))
    elif chart_type == "pie":
        st.plotly_chart(px.pie(df, names=categorical_columns[0], values=numerical_columns[0], title="Pie Chart"))

# Button to ask the question and retrieve data
submit = st.button("Ask the question")

# Ensure that generated SQL query and dataframe persist across button clicks
if submit:
    # Generate the SQL query using Gemini
    response = get_gemini_response(question, prompt)
    st.session_state['generated_query'] = response
    st.write(f"Generated SQL/Query: {response}")

    # Query the database based on the generated SQL
    df = read_database_query(response, db_type, db_params)
    
    if not df.empty:
        st.session_state['df'] = df  # Store the dataframe in session_state

# Display the results and generated query if available in session_state
st.subheader("Query Results")
if 'generated_query' in st.session_state:
    st.write(f"Generated SQL/Query: {st.session_state['generated_query']}")
if 'df' in st.session_state and not st.session_state['df'].empty:
    st.write(st.session_state['df'])
else:
    st.write("No results found or an error occurred.")

# Visualization section
if 'df' in st.session_state and not st.session_state['df'].empty:
    st.subheader("Visualization")
    
    # Allow user to select chart type before plotting
    chart_type = st.selectbox("Select Chart Type", ["line", "bar", "pie"], key="chart_type")

    # Button to trigger plotting
    if st.button("Plot"):
        visualize_data(st.session_state['df'], chart_type)
