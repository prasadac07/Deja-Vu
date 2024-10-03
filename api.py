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

# def get_gemini_response_sqllite(question, prompt, context):
#     model = genai.GenerativeModel('gemini-pro')
#     question = question + context
#     response = model.generate_content([prompt[0], question])
#     return response.text

def get_gemini_response_sqllite(question, prompt, context):
    try:

        # Ensure API key is set
        if not os.getenv("GOOGLE_API_KEY"):
            print("Error: GOOGLE_API_KEY is not set.")
            return None

        model = genai.GenerativeModel('gemini-pro')

        # Combine question with context
        question_with_context = f"{question} {context}"

        # Log the final question and context
        print(f"Question passed to Gemini: {question_with_context}")

        # Make the API call
        response = model.generate_content([prompt[0], question_with_context])

        # Log and check the response
        print(f"Gemini API response: {response}")

        if response and hasattr(response, 'text'):
            return response.text
        else:
            print("Error: Gemini API did not return valid text.")
            return None

    except Exception as e:
        print(f"Error while calling Gemini API: {e}")
        return None





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
# def generate_query():
#     data = request.get_json()
#     question = data.get('questionInput')
#     type = data.get('dbType')
#     response = None

#     print(data)
#     if not question:
#         return jsonify({'error': 'Missing question parameter'}), 400
    
#     if type == 'sqllite':
#         response = get_gemini_response_sqllite(question, prompt, chatbot_context)
    
#     # print(response)
#     return jsonify({'query': response})

@app.route('/generate_query', methods=['POST'])
def generate_query():
    parse_db_file("./sqllite_1.db")
    print(chatbot_context)
    data = request.get_json()
    print("Here is the dataType: ",(data))
    question = data.get('questionInput')
    db_type = data.get('dbType')  # Correct the spelling here if needed
    

    if not question:
        return jsonify({'error': 'Missing question parameter'}), 400
    
    # Ensure response is always initialized
    response = None

    # Check if the db_type is 'sqlite'
    if db_type == 'sqlite':
        context = chatbot_context.get('db_data', "")  # Get context or default to empty
        response = get_gemini_response_sqllite(question, prompt, context)
        print('Hello')

    print(f"Generated SQL query: {response}")  # Log the generated query for debugging

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
        
        print("Database parsed successfully and context updated.")

    except sqlite3.Error as e:
        print(f"Error parsing .db file: {e}")

parse_db_file("./sqllite_1.db")


# # API endpoint to execute query and return results
# @app.route('/execute_query', methods=['POST'])
# @app.route('/execute_query', methods=['POST'])
# def execute_query():
#     data = request.get_json()
#     query = data.get('query')
#     db_type = data.get('dbType')
#     db_params = data.get('dbParams')
    
#     if not query or not db_type or not db_params:
#         return jsonify({'error': 'Missing query, db_type, or db_params parameters'}), 400

#     print(query, db_type, db_params)
    
#     # Execute the query on the database
#     parse_db_file("E:\Pulzion Hackathon\sqllite_1.db")
#     results = read_database_query(query, db_type, db_params)

#     num_results = len(results)
#     print(num_results)
    
#     if num_results == 0:
#         response = "No results found."
#         summary = "No results found for the query."
#     elif num_results == 1:
#         response = f"Found one record: {results[0]}."
#         summary = get_gemini_response(str(results[0]), ["Summarize the following database record:"])
#     else:
#         response = f"Found {num_results} records. The first few are: {results[:5]}."
#         summary = get_gemini_response(str(results[:5]), ["Summarize the following database records:"])

#     return jsonify({'results': results, 'natural_language_response': response, 'summary': summary})

@app.route('/execute_query', methods=['POST'])
def execute_query():
    data = request.get_json()
    
    # Extract query, dbType, and dbParams from the request body
    query = data.get('query')
    db_type = data.get('dbType')
    print(db_type)
    db_params = data.get('dbParams')
    
    # Log the received data for debugging
    print(f"Received data: {data}")
    
    # Check if all required parameters are present
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400
    if not db_type:
        return jsonify({'error': 'Missing dbType parameter'}), 400
    if not db_params:
        return jsonify({'error': 'Missing dbParams parameter'}), 400

    # Log query, db_type, and db_params for debugging
    print(f"Query: {query}")
    print(f"Database Type: {db_type}")
    print(f"Database Params: {db_params}")

    # Execute the query on the database
    results = read_database_query(query, db_type, db_params)
    
    # if error:
    #     return jsonify({'error': error}), 500

    num_results = len(results)
    print(f"Number of results: {num_results}")

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
