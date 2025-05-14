import psycopg2
import os


# PostgreSQL connection parameters
pg_conn_params = {
  "dbname": os.getenv("POSTGRESDB_NAME"),
  "user": os.getenv("POSTGRESDB_USER"),
  "password": os.getenv("POSTGRESDB_PASS"),
  "host": "postgres",
  "port": 5432,
}


# Function to connect to PostgreSQL
def get_pg_connection():
  return psycopg2.connect(**pg_conn_params)