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
def insert_data(conn, table, key_column, columns, rows):
  key_index = columns.index(key_column)
  offset = 0
  for row in rows:
    row[key_index] = row[key_index] + offset
    while True:
      try:
        with conn.cursor() as cursor:
          placeholders = ", ".join(["%s"] * len(row))
          columns_list = ", ".join(columns)
          sql = f"INSERT INTO {table} ({columns_list}) VALUES ({placeholders})"
          cursor.execute(sql, row)
        conn.commit()
        break
      except:
        conn.rollback()
        print(f"Offset: {offset}")
        last_id = row[key_index] + offset
        #row[key_index] = last_id + 1
        row[key_index] = generate_new_id(set({last_id}))
        offset += 1


# Function to generate a new unique ID
def generate_new_id(existing_ids):
  new_id = max(existing_ids) + 1
  existing_ids.add(new_id)
  return new_id


# Remover chave primaria
def remove_primary_key(columns, rows, primary_key):
  if primary_key not in columns:
    return columns, rows

  pk_index = columns.index(primary_key)
  new_columns = [col for i, col in enumerate(columns) if i != pk_index]
  new_rows = [
    [value for i, value in enumerate(row) if i != pk_index] for row in rows
  ]
  return new_columns, new_rows


# Function to duplicate data
def duplicate_data(conn, table, key_column, multiplier):
  columns, rows = fetch_data(conn, table)
  key_index = columns.index(key_column)
  existing_ids = {row[columns.index(key_column)] for row in rows}

  new_rows = []
  for i in range(multiplier - 1):
    for row in rows:
      new_row = list(row)
      new_row[key_index] = generate_new_id(existing_ids)
      new_rows.append(new_row)

  insert_data(conn, table, key_column, columns, new_rows)