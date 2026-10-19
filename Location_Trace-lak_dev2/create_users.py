import os
import psycopg2
from passlib.context import CryptContext
import getpass
import re

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "location_tracker"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "root")
}

# Password hashing with explicit py-bcrypt backend (uncomment if needed)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__backend="pybcrypt")

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connection established.")
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        raise

def init_users_table_if_not_exists(conn):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users');")
            if not cur.fetchone()[0]:
                print("Users table not found, creating it...")
                cur.execute("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        hashed_password VARCHAR(255) NOT NULL
                    );
                """)
                conn.commit()
                print("Users table created.")
            else:
                print("Users table already exists.")
    except psycopg2.Error as e:
        print(f"Error initializing users table: {e}")
        conn.rollback()
        raise

def add_user(conn, username, password):
    try:
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", username):
            print(f"Invalid email format: {username}")
            return False
        hashed_password = pwd_context.hash(password)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, hashed_password)
                VALUES (%s, %s)
                ON CONFLICT (username) DO NOTHING
                RETURNING id;
            """, (username, hashed_password))
            result = cur.fetchone()
            conn.commit()
            if result:
                print(f"User {username} added successfully.")
                return True
            else:
                print(f"User {username} already exists.")
                return False
    except psycopg2.Error as e:
        print(f"Error adding user: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"Error hashing password: {e}")
        return False

def main():
    try:
        conn = get_db_connection()
        init_users_table_if_not_exists(conn)
        while True:
            username = input("Enter username (email) (or 'quit' to exit): ").strip()
            if username.lower() == 'quit':
                break
            if not username:
                print("Username cannot be empty.")
                continue
            password = getpass.getpass("Enter password: ").strip()
            if not password:
                print("Password cannot be empty.")
                continue
            if add_user(conn, username, password):
                print("User creation successful.")
            else:
                print("User creation failed.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()