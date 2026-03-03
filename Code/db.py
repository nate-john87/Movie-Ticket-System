import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "movieapp",
    "password": "MovieAppPass123!",
    "database": "movie_ticket_db",
}

def get_conn():
    return mysql.connector.connect(**DB_CONFIG)