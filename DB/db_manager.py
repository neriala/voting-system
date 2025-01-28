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
    initialize_db()
    #for _ in range(10):
    #    national_id = generate_valid_national_id()
    #    center_id = (int(national_id[-1]) % 3) + 1  
    #    add_voter(national_id, center_id)

   

    add_voter("430588319", 1)
    add_voter("124141813", 1)
    add_voter("425626603", 1)
    add_voter("673161303", 1)
    add_voter("087215240", 1)
    add_voter("296386709", 1)
    add_voter("294146006", 1)
    add_voter("924612419", 1)
    add_voter("531944379", 1)
    add_voter("734941289", 1)
    


    add_voter("710004557", 2)
    add_voter("442201877", 2)
    add_voter("352962831", 2)
    add_voter("096029814", 2)
    add_voter("509638037", 2)
    add_voter("249903204", 2)
    add_voter("335377701", 2)
    add_voter("402214357", 2)
    add_voter("676090111", 2)
    add_voter("461375941", 2)
    
    add_voter("868753278", 3)
    add_voter("505415695", 3)
    add_voter("555595628", 3)
    add_voter("060303658", 3)
    add_voter("973382682", 3)
    add_voter("970632998", 3)
    add_voter("784859068", 3)
    add_voter("879949295", 3)
    add_voter("405699745", 3)
    add_voter("192978815", 3)
    



    # add_voter("907937973", 1)
    # add_voter("668133820", 1)
    # add_voter("233638386", 1)
    # add_voter("216788349", 1)
    # add_voter("462112079", 1)

    # add_voter("128663887", 2)
    # add_voter("394357651", 2)
    # add_voter("526376777", 2)
    # add_voter("850058207", 2)
    # add_voter("208030387", 2)

    # add_voter("673049045", 3)
    # add_voter("816002695", 3)
    # add_voter("089067615", 3)
    # add_voter("024271488", 3)
    # add_voter("128010238", 3)