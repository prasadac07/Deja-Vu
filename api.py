from dotenv import load_dotenv
load_dotenv()  # Load all environment variables

import os
import sqlite3
import psycopg2  # For PostgreSQL
import mysql.connector  # For MySQL
from pymongo import MongoClient  # For MongoDB
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
CORS(app)
# Function to load Google Gemini Model and provide queries as response
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text

# Function to connect and query SQLite
def read_sqlite_query(sql, db):
   
    print(sql, db)
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        return rows
    except sqlite3.Error as e:
        print(e)
        return [], f"SQLite error: {e}"
    finally:
        conn.close()  # Ensure connection is closed

# Function to connect and query PostgreSQL
def read_postgresql_query(sql, db_params):
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        return rows, None
    except psycopg2.Error as e:
        return [], f"PostgreSQL error: {e}"
    finally:
        if conn:
            cur.close()
            conn.close()

# Function to connect and query MySQL
def read_mysql_query(sql, db_params):
    try:
        conn = mysql.connector.connect(**db_params)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        return rows, None
    except mysql.connector.Error as e:
        return [], f"MySQL error: {e}"
    finally:
        if conn:
            cur.close()
            conn.close()

# Function to query MongoDB
def read_mongodb_query(collection_name, query, db_params):
    try:
        client = MongoClient(db_params['host'], db_params['port'])
        db = client[db_params['database']]
        collection = db[collection_name]
        results = collection.find(query)
        return list(results), None
    except Exception as e:
        return [], f"MongoDB error: {e}"
    finally:
        if client:
            client.close()

# Function to choose database and query
def read_database_query(sql, db_type, db_params):
    if db_type == 'sqlite':
        print("HERE",sql, db_params['db'])
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
        return [], "Invalid database type"

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

# API endpoint to generate SQL query
@app.route('/generate_query', methods=['POST'])
def generate_query():
    data = request.get_json()
    question = data.get('questionInput')
    print(data)
    if not question:
        return jsonify({'error': 'Missing question parameter'}), 400
    
    response = get_gemini_response(question, prompt)
    print(response)
    return jsonify({'query': response})

# API endpoint to execute query and return results
@app.route('/execute_query', methods=['POST'])
def execute_query():
    data = request.get_json()
    query = data.get('query')
    db_type = data.get('dbType')
    db_params = data.get('dbParams')
    if not query or not db_type or not db_params:
        return jsonify({'error': 'Missing query, db_type, or db_params parameters'}), 400

    print(query, db_type, db_params)
    results= read_database_query(query, db_type, db_params)
  

    # Generate natural language response and summary using Gemini
    num_results = len(results)
    print(num_results)
    if num_results == 0:
        response = "No results found."
        summary = "No results found for the query."
    elif num_results == 1:
        response = f"Found one record: {results[0]}."
        summary = get_gemini_response(str(results[0]), ["Summarize the following database record:"])
    else:
        response = f"Found {num_results} records. The first few are: {results[:5]}."
        summary = get_gemini_response(str(results[:5]), ["Summarize the following database records:"])
    
    return jsonify({'results': results, 'natural_language_response': response, 'summary': summary})

if __name__ == '__main__':
    app.run(debug=True)
