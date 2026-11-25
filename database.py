import os
import re
import mysql.connector
from mysql.connector import errorcode
from config import Config


def get_connection():
    return mysql.connector.connect(**Config.MYSQL)


def initialize_schema():
    settings = dict(Config.MYSQL)
    database_name = settings["database"]
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise ValueError("MYSQL_DATABASE may contain only letters, numbers, and underscores")

    try:
        conn = mysql.connector.connect(**settings)
    except mysql.connector.Error as exc:
        if exc.errno != errorcode.ER_BAD_DB_ERROR:
            raise

        server_settings = dict(settings)
        server_settings.pop("database")
        conn = mysql.connector.connect(**server_settings)
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            conn.commit()
        finally:
            conn.close()
        conn = mysql.connector.connect(**settings)

    try:
        cursor = conn.cursor()
        schema_path = os.path.join(os.path.dirname(__file__), "database", "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as schema_file:
            for statement in schema_file.read().split(";"):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query, params=None):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        conn.close()


def fetch_one(query, params=None):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        conn.close()


def execute(query, params=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
