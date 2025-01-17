import sqlite3

def init_db():
    with sqlite3.connect("voting.db") as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS voters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                national_id TEXT UNIQUE NOT NULL,
                has_voted BOOLEAN DEFAULT 0
            )
        ''')
        print("Table 'voters' created or already exists.")

def add_voter(national_id):
    with sqlite3.connect("voting.db") as conn:
        try:
            conn.execute("INSERT INTO voters (national_id) VALUES (?)", (national_id,))
            conn.commit()
            print(f"Voter with ID {national_id} added successfully.")
        except sqlite3.IntegrityError:
            print(f"Voter with ID {national_id} already exists.")



if __name__ == "__main__":
    init_db()
    add_voter("318638566")
    add_voter("987654321")
    add_voter("111222333")
