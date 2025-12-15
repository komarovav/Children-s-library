import pymysql

def get_connection():
    return (pymysql.connect
            ( host="5.183.188.132",
              port=3306,
              user="2025_mysql__usr7",
              password="7LsDRBDX7z1v3s9S",
              database="2025_mysql_ver",
              cursorclass=pymysql.cursors.DictCursor,
              autocommit=True ))