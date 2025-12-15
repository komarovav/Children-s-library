from db import get_connection

def fetch_all(table_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    conn.close()
    return rows, columns

def insert_row(table, values):
    conn = get_connection()
    cur = conn.cursor()
    cols = ", ".join(values.keys())
    placeholders = ", ".join(["%s"] * len(values))
    query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders});"
    cur.execute(query, list(values.values()))
    conn.commit()
    conn.close()

def update_row(table, record_id, values, primary_key="id"):
    conn = get_connection()
    cur = conn.cursor()
    set_clause = ", ".join([f"{col} = %s" for col in values.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {primary_key} = %s"
    params = list(values.values()) + [record_id]
    cur.execute(query, params)
    conn.commit()
    conn.close()

def delete_row(table, record_id, primary_key="id"):
    conn = get_connection()
    cur = conn.cursor()
    query = f"DELETE FROM {table} WHERE {primary_key} = %s"
    cur.execute(query, (record_id,))
    conn.commit()
    conn.close()

