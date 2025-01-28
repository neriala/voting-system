import sqlite3
import os

# נתיב למסד הנתונים
DB_PATH = r"C:\voting-system\DB\voting.db"

# 1. אתחול מסד הנתונים
def initialize_db():
    """Initializes the database and creates the required tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # טבלת מצביעים
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_id TEXT UNIQUE NOT NULL,
            has_voted BOOLEAN NOT NULL DEFAULT 0,
            center_id INTEGER NOT NULL
        )
    """)

    # טבלת הצבעות
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
            encrypted_vote TEXT NOT NULL,
            center_id INTEGER NOT NULL,
            nonce TEXT UNIQUE,
            vote_hash TEXT
        )
    """)

    # טבלת תוצאות ספירה
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

# 2. הוספת מצביע חדש
def add_voter(national_id, center_id):
    """Adds a new voter to the database."""
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

# 3. עדכון סטטוס הצבעה
def update_voter_status(national_id):
    """Updates the voting status of a voter."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE voters
        SET has_voted = 1
        WHERE national_id = ?
    """, (national_id,))
    conn.commit()
    conn.close()
    print(f"Voter with ID {national_id} marked as voted.")

# 4. הוספת הצבעה מוצפנת
def add_vote(encrypted_vote, center_id):
    """Adds an encrypted vote to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO votes (encrypted_vote, center_id)
        VALUES (?, ?)
    """, (encrypted_vote, center_id))
    conn.commit()
    conn.close()
    print(f"Vote added successfully for center {center_id}.")

# 5. אחזור תוצאות לפי מרכז ספירה
def get_votes_by_center(center_id):
    """Fetches all votes for a specific center."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT encrypted_vote FROM votes
        WHERE center_id = ?
    """, (center_id,))
    votes = cursor.fetchall()
    conn.close()
    return [vote[0] for vote in votes]

# 6. אחזור תוצאות הספירה
def get_tally_results():
    """Fetches the tally results for all centers."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT center_id, result FROM tally_results
    """)
    results = cursor.fetchall()
    conn.close()
    return results

import random

def is_valid_national_id(id_number):
    """בודק האם מספר ת"ז תקין לפי הפונקציה שניתנה"""
    if len(id_number) != 9 or not id_number.isdigit():
        return False

    counter = 0
    for i in range(9):
        digit = int(id_number[i]) * ((i % 2) + 1)  # הכפלת הספרה
        if digit > 9:
            digit -= 9
        counter += digit

    return counter % 10 == 0

def generate_valid_national_id():
    """מייצר מספר ת"ז תקין"""
    while True:
        id_number = ''.join(str(random.randint(0, 9)) for _ in range(9))  # יצירת מספר ת"ז רנדומלי
        if is_valid_national_id(id_number):
            return id_number

import hashlib

# יצירת 10 משתמשים עם מספרי ת"ז תקינים
def hash_national_id(national_id):
    """Hashes the entire national ID."""
    return hashlib.sha256(national_id.encode()).hexdigest()

def update_database_with_hashed_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # שליפת כל הת"ז הגולמיות
    cursor.execute("SELECT national_id, has_voted FROM voters")
    voters = cursor.fetchall()

    # עדכון הת"ז המוצפנות
    for national_id, has_voted in voters:
        hashed_id = hash_national_id(national_id)
        cursor.execute(
            "UPDATE voters SET national_id = ? WHERE national_id = ?",
            (hashed_id, national_id),
        )
    
    conn.commit()
    conn.close()



if __name__ == "__main__":
    # הפעלת פונקציות בדיקה
    initialize_db()
    #add_voter("123456789", 1)
    #add_voter("318638566", 2)
    #add_voter("213152390", 2)
    for _ in range(10):
        national_id = generate_valid_national_id()
        center_id = (int(national_id[-1]) % 3) + 1  # מספר מרכז רנדומלי בין 1 ל-3
        add_voter(national_id, center_id)

    #update_database_with_hashed_ids()