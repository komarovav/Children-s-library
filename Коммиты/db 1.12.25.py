import pymysql

def get_connection():
    return (pymysql.connect
            ( host="host",
              port=port,
              user="user",
              password="password",
              database="database",
              cursorclass=pymysql.cursors.DictCursor,

              autocommit=True ))
