import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
from fastapi import HTTPException

MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'LEMONA_GMP',
    'user': 'root',
    'password': '1234',
    'port': 3306,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

@contextmanager
def get_db_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        yield connection
    except Error as e:
        print(f"MySQL 연결 오류: {e}")
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="데이터베이스 연결 오류")
    finally:
        if connection and connection.is_connected():
            connection.close()