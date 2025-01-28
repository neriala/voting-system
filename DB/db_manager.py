import sqlite3
import os

DB_PATH = r"C:\voting-system\DB\voting.db"


def initialize_db():
    """Initializes the database and creates the required tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_id TEXT UNIQUE NOT NULL,
            has_voted BOOLEAN NOT NULL DEFAULT 0,
            center_id INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
            encrypted_vote TEXT NOT NULL,
            center_id INTEGER NOT NULL,
            nonce TEXT UNIQUE,
            vote_hash TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tally_results (
            tally_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            center_id INTEGER NOT NULL,                
            candidate TEXT NOT NULL,                  
            vote_count INTEGER NOT NULL,             
            result_hash TEXT NOT NULL,             
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully!")


def add_voter(national_id, center_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO voters (national_id, has_voted, center_id)
            VALUES (?, 0, ?)
        """, (national_id, center_id))
        conn.commit()
        conn.close()
        print(f"Voter with ID {national_id} added successfully!")
    except sqlite3.IntegrityError:
        print(f"Voter with ID {national_id} already exists.")




import random
import hashlib

def is_valid_national_id(id_number):
    if len(id_number) != 9 or not id_number.isdigit():
        return False

    counter = 0
    for i in range(9):
        digit = int(id_number[i]) * ((i % 2) + 1)  
        if digit > 9:
            digit -= 9
        counter += digit

    return counter % 10 == 0

def generate_valid_national_id():
    while True:
        id_number = ''.join(str(random.randint(0, 9)) for _ in range(9))  
        if is_valid_national_id(id_number):
            return id_number





if __name__ == "__main__":
    #initialize_db()
    for _ in range(10):
        national_id = generate_valid_national_id()
        center_id = (int(national_id[-1]) % 3) + 1  
        add_voter(national_id, center_id)

   

    add_voter("422411736", 1)
    add_voter("525538146", 1)
    add_voter("790579486", 1)
    add_voter("843150129", 1)
    add_voter("265292490", 1)

    add_voter("269553541", 2)
    add_voter("364782607", 2)
    add_voter("050471887", 2)
    add_voter("948355557", 2)
    add_voter("173130857", 2)

    add_voter("840140925", 3)
    add_voter("810433292", 3)
    add_voter("294343728", 3)
    add_voter("100562065", 3)
    add_voter("575251418", 3)