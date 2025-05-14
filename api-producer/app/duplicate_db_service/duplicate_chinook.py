from ..client.postgres_client import get_pg_connection


def duplicate_albums():
  connection = get_pg_connection()
  tables_to_duplicate = [
    ("album", "album_id"),
  ]
  multiplier = 2  # Number of times to duplicate the data

  try:
    for table, key_column in tables_to_duplicate:
      print(f"Duplicating data in {table}...")
      duplicate_data(connection, table, key_column, multiplier)
    print("Data duplication complete.")
  finally:
    connection.close()


# Function to fetch data from a table
def fetch_data(conn, table):
  with conn:
    with conn.cursor() as cursor:
      cursor.execute(f"SELECT * FROM {table}")
      columns = [desc[0] for desc in cursor.description]
      rows = cursor.fetchall()
      return columns, rows


# Function to insert data into a table
def insert_data(conn, table, columns, rows):
  with conn.cursor() as cursor:
    for row in rows:
      placeholders = ", ".join(["%s"] * len(row))
      columns_list = ", ".join(columns)
      sql = f"INSERT INTO {table} ({columns_list}) VALUES ({placeholders})"
      cursor.execute(sql, row)
  conn.commit()


# Function to generate a new unique ID
def generate_new_id(existing_ids):
  while True:
    new_id = max(existing_ids) + 1
    if new_id not in existing_ids:
      existing_ids.add(new_id)
      return new_id


# Function to duplicate data
def duplicate_data(conn, table, key_column, multiplier):
  columns, rows = fetch_data(conn, table)
  existing_ids = {row[columns.index(key_column)] for row in rows}

  new_rows = []
  for i in range(multiplier - 1):
    for row in rows:
      new_row = list(row)
      new_row[columns.index(key_column)] = generate_new_id(existing_ids)
      new_rows.append(new_row)

  insert_data(conn, table, columns, new_rows)