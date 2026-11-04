"""
test_db.py

A quick test that the database connection works.
Connects to Supabase, asks for the PostgreSQL version, and prints it.
Nothing is read from or written to your tables.
"""

import os                       # lets us read environment variables
from dotenv import load_dotenv  # reads variables from the .env file
import psycopg2                 # the PostgreSQL driver for Python

# Load DATABASE_URL from .env, so the password stays out of the code.
load_dotenv()

# Open a connection using the full connection string.
# os.environ["DATABASE_URL"] raises a KeyError if the variable is missing,
# which is a quick way to spot a typo in .env.
conn = psycopg2.connect(os.environ["DATABASE_URL"])

# A cursor is the object that sends SQL to the database and holds results.
cur = conn.cursor()

# A harmless query that every PostgreSQL database can answer.
cur.execute("select version();")

# fetchone() returns the first row of the result as a tuple.
print(cur.fetchone())

# Always close the connection when you're done, to free it up on the server.
conn.close()