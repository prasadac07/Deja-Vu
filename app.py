from dotenv import load_dotenv
load_dotenv()  # Load all environment variables

import os
import sqlite3
import psycopg2  # For PostgreSQL
import mysql.connector  # For MySQL
from pymongo import MongoClient  # For MongoDB
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json 
app = Flask(__name__)
CORS(app)

def get_worqhat_response_nano(question=" ", prompt=" ", context=" ", model="nano"):
    prompt_text = prompt[0] if prompt[0] is not None else ""
    question = question if question is not None else ""
    context = context if context is not None else ""

    url = "https://api.worqhat.com/api/ai/content/v4"
    payload = json.dumps({
    "question": prompt[0] + "Here is the user question: "+ question +"Here is the db context: "+ context ,
    "model": f"aicon-v4-{model}-160824",
    "randomness": 0.1,
    "stream_data": False,
    "training_data": "You are an expert SQL bot",
    "response_type": "text"
    })
    headers = {
    'User-Agent': 'Apidog/1.0.0 (https://apidog.com)',
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {os.getenv("WORQHAT_API_KEY")}'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    # print(response.text)
    resp = json.loads(response.text)
    # print("JSON STRUCC: ",resp["content"])
    return resp["content"]


correctionPrompt = ["""
You are an expert in converting English questions to SQL query! You have to correct the following query. 
I am also giving you the error caused by it. Return only the sql query without anything else.
 Return only one query without any quotations
"""]
# Function to connect and query SQLite
def read_sqlite_query(sql, db, attempts=2):  # Added attempts parameter
    print(sql, db)
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        return rows, sql
    except sqlite3.Error as e:
        print(e)
        if attempts > 0:
            print("Attempting to correct the query...")
            question = "I am getting an error while executing the following query: " + sql + "The error is: " + str(e)
            newQuery = get_worqhat_response_nano(question, correctionPrompt[0], db, "large")
            # print(newQuery)
            return read_sqlite_query(newQuery, db, attempts - 1)  # Recursive call
        else:
            return [], f"SQLite error: {e}"
    finally:
        conn.close()  # Ensure connection is closed



# Function to connect and query MySQL
def read_mysql_query(sql, db_params, attempts=2):
    try:
        conn = mysql.connector.connect(**db_params)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        return rows, sql
    except mysql.connector.Error as e:
        print(e)
        if attempts > 0:
            print("Attempting to correct the query...")
            question = "I am getting an error while executing the following query: " + sql + "The error is: " + str(e)
            s = " ".join([str(item) for item in db_params.values()])
            newQuery = get_worqhat_response_nano(question, correctionPrompt[0], s, "large")
            # print(newQuery)
            return read_mysql_query(newQuery, db_params, attempts - 1)  # Recursive call
        else:
            return [], f"SQLite error: {e}"
        
    finally:
        if conn:
            cur.close()
            conn.close()

# Function to query MongoDB


# Function to choose database and query
def read_database_query(sql, db_type, db_params):
    if db_type == 'sqlite':
        # print("HERE",sql, db_params['db'])
        return read_sqlite_query(sql, db_params['db'])

    elif db_type == 'mysql':
        return read_mysql_query(sql, db_params)
  
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
    Return only the sql query without anything else. Return only one query without any quotations
    Example output: SELECT * from employees.
    Example wrong output: ```sql: SELECT * from books```
    """
]

# API endpoint to generate SQL query
@app.route('/generate_query', methods=['POST'])
def generate_query():
    data = request.get_json()
    # print("Here is the dataType: ",(data))
    question = data.get('questionInput')
    db_type = data.get('dbType')  # Correct the spelling here if needed
    db_params = data.get('dbParams') # Get MySQL connection parameters
    
    if not question:
        return jsonify({'error': 'Missing question parameter'}), 400
    
    # Ensure response is always initialized
    response = None

    # Check if the db_type is 'sqlite'
    if db_type == 'sqlite':
        parse_db_file("./sqllite_1.db")
        context = get_database_summary(chatbot_context.get('db_data', ""))  # Get context or default to empty
        print("THIS IS CONTEXT: ",context)
        response = get_worqhat_response_nano(question, prompt, context, "large")
    # Check if the db_type is 'mysql'
    elif db_type == 'mysql':
        context = get_database_summary(parse_mysql_db(db_params))  # Get context from MySQL
        response = get_worqhat_response_nano(question, prompt, context, "large")

    # print(f"Generated SQL query: {response}") 

    if response is None:
        return jsonify({'error': 'Failed to generate query response'}), 500

    return jsonify({'query': response})

chatbot_context = {}

def parse_db_file(db_file_path):
    """
    Parse the SQLite .db file and update the chatbot context with the data.
    
    Args:
    db_file_path (str): The path to the SQLite database file.
    
    Returns:
    None
    """
    global chatbot_context

    try:
        # Connect to the SQLite database file
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()

        # Fetch the list of all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Initialize the context data structure
        db_data = {}
        
        for table_name in tables:
            # Get table name from the tuple
            table_name = table_name[0]
            
            # Fetch all rows from the table
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()

            # Fetch the column names
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Store the table's data in the context
            db_data[table_name] = {
                'columns': columns,
                'rows': rows
            }

        # Update chatbot context with the parsed database content
        chatbot_context['db_data'] = db_data
        chatbot_context['summary'] = f"Parsed {len(tables)} tables from the database."
        
        # print("Database parsed successfully and context updated.")

    except sqlite3.Error as e:
        print(f"Error parsing .db file: {e}")


# Function to parse MySQL database and build context
def parse_mysql_db(db_params):
    try:
        conn = mysql.connector.connect(**db_params)
        cursor = conn.cursor()

        # Fetch the list of all tables in the database
        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]

        # Initialize the context data structure
        db_data = {}

        for table_name in tables:
            # Fetch all rows from the table
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()

            # Fetch the column names
            cursor.execute(f"DESCRIBE {table_name};")
            columns = [col[0] for col in cursor.fetchall()]

            # Store the table's data in the context
            db_data[table_name] = {
                'columns': columns,
                'rows': rows
            }

        return db_data

    except mysql.connector.Error as e:
        print(f"Error parsing MySQL database: {e}")
        return {}  # Return an empty dictionary if parsing fails
    finally:
        if conn:
            cursor.close()
            conn.close()

def get_database_summary(db_data):
    """
    Generates a summary of the database schema using WorqHat LLM.

    Args:
        db_data (dict): A dictionary containing the database schema.

    Returns:
        str: A summary of the database schema.
    """

    # Construct the prompt for the WorqHat LLM
    prompt = f"""
    You are an AI assistant that can summarize database schemas.

    Here's the database schema:
    {db_data}

    Please provide a concise summary of the database schema, including:
    - The number of tables.
    - The names of the tables and their columns.
    - Don't include any sample data or rows.
    """

    # Call the get_worqhat_response function to generate the summary
    summary = get_worqhat_response_nano("", [prompt], "", "nano")

    return summary


@app.route('/execute_query', methods=['POST'])
def execute_query():
    data = request.get_json()
    
    # Extract query, dbType, and dbParams from the request body
    query = data.get('query')
    db_type = data.get('dbType')
    # print(db_type)
    db_params = data.get('dbParams')
    
    # Log the received data for debugging
    # print(f"Received data: {data}")
    
    # Check if all required parameters are present
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400
    if not db_type:
        return jsonify({'error': 'Missing dbType parameter'}), 400
    if not db_params:
        return jsonify({'error': 'Missing dbParams parameter'}), 400

   

    # Execute the query on the database
    results, sql = read_database_query(query, db_type, db_params)
    print(sql)
    num_results = len(results)
    # print(f"Number of results: {num_results}")

    if num_results == 0:
        response = "No results found."
        summary = "No results found for the query."
    elif num_results == 1:
        response = f"Found one record: {results[0]}"
        summary = f"Found one record."
    else:
        response = f"Found {num_results} records."
        summary = f"Found {num_results} records."

    prompt = [
        """You are an AI assistant that explains SQL queries and their results.

        Please provide a clear and concise explanation of what the query does. 
        Explain it in a way that someone who doesn't know SQL can understand.
        Dont include *s in response."""
    ]
# Generate explanation using Gemini
    print("Here is the question, ",data.get('query'))
    question = "Here is the sql query: " + data.get('query') 
    s = ', '.join([str(item) for item in results])
    explanation = get_worqhat_response_nano(question, prompt , s, "large")

    # Prepare the JSON response
    return jsonify({
        'results': results,
        'summary': summary,
        'sql_query': sql,
        'natural_language_response': explanation  # Include the explanation in the response
    })


if __name__ == '__main__':
    app.run(debug=True)
