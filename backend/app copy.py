from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import networkx as nx
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import json
import hashlib

# משתנים לאחסון פרמטרי DH
DH_PARAMS = {"p": 8262525019121781265000801114122156349216670389155538325999152622344144720466698306297330225964244933192417628506609441718343308145224722902681373613370087, "g": 2}  # ערכים בסיסיים, ניתן להחליף באלו שמתאימים יותר
SERVER_PRIVATE_KEY = 4  # מפתח פרטי שרת
SERVER_PUBLIC_KEY = (DH_PARAMS["g"] ** SERVER_PRIVATE_KEY) % DH_PARAMS["p"]  # מפתח ציבורי שרת
SHARED_KEY = None


app = Flask(__name__)
CORS(app)  # אפשר תקשורת בין React ל-Flask

# נתיב מסד הנתונים
DB_PATH = r"C:\voting-system\DB\voting.db"



def get_voter_status_by_graph(received_encrypted_graph):
    """Checks if the encrypted graph matches any hashed national ID in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # שליפת כל הת"ז והסטטוסים מבסיס הנתונים
    cursor.execute("SELECT national_id, has_voted FROM voters")
    voters = cursor.fetchall()
    conn.close()

    print("Voters in DB:", voters)

    for national_id, has_voted in voters:
        # יצירת גרף עבור תעודת זהות מבסיס הנתונים
        database_graph = generate_graph_from_id(national_id)
        print(f"Checking ID: {national_id}")
        print(database_graph)

        # חישוב SHA-256 עבור הגרף שנוצר
        database_encrypted_graph = compute_sha256(database_graph)

        # הדפסות למעקב
        
        print(f"Received Encrypted Graph: {received_encrypted_graph}")
        print(f"Database Encrypted Graph: {database_encrypted_graph}")

        # השוואת ההצפנה של הגרף המתקבל לזו שנמצאת בבסיס הנתונים
        if received_encrypted_graph == database_encrypted_graph:
            print(f"Match found for ID {national_id}. Voted: {has_voted}")
            return national_id, has_voted

    return None, None


def mark_voter_as_voted(national_id):
    """Marks a voter as having voted."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE voters SET has_voted = 1 WHERE national_id = ?", (national_id,))
    conn.commit()
    conn.close()




def add_encrypted_vote(encrypted_vote, center_id, nonce):
    """
    שמירת ההצבעה המוצפנת בבסיס הנתונים עם hash
    """
    vote_hash = generate_vote_hash(encrypted_vote, nonce, center_id)  # יצירת ה-hash
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO votes (encrypted_vote, center_id, nonce, vote_hash) VALUES (?, ?, ?, ?)",
        (encrypted_vote, center_id, nonce, vote_hash),
    )
    conn.commit()
    conn.close()




### פונקציות ליצירת גרפים
def generate_graph_from_id(id_number):
    """Generates a graph from an ID and returns its nodes and edges."""
    graph = {"nodes": [], "edges": []}

    # יצירת צמתים ייחודיים
    nodes = list(set(int(char) for char in id_number))
    graph["nodes"] = nodes

    # יצירת קשתות בין ספרות סמוכות
    edges = []
    for i in range(len(id_number) - 1):
        edge = (int(id_number[i]), int(id_number[i + 1]))
        edges.append(edge)
    graph["edges"] = edges

    return graph


def compute_sha256(graph):
    """Computes the SHA-256 of the graph."""
    # המרת כל הטאפלים ברשימה לרשימות (JSON אינו תומך בטאפלים)
    graph["edges"] = [list(edge) for edge in graph["edges"]]

    # המרת הגרף למחרוזת JSON מסודרת
    graph_string = json.dumps(graph, separators=(",", ":"))
    print(graph_string)
    return hashlib.sha256(graph_string.encode()).hexdigest()



### נקודות קצה (Endpoints)
@app.route('/vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    graph_data = data.get("encryptedGraph")
    encrypted_vote = data.get("encrypted_vote")
    center_id = data.get("center_id")
    if not graph_data or not encrypted_vote or not center_id:
        return jsonify({"status": "error", "message": "Missing data."}), 400


    # בדיקת איזומורפיזם מול בסיס הנתונים
    national_id, has_voted = get_voter_status_by_graph(graph_data)


    # פענוח ההצבעה
    decrypted_vote = decrypt_vote(encrypted_vote, SHARED_KEY)

    if not decrypted_vote:
        return jsonify({"status": "error", "message": "Failed to decrypt vote."}), 500

    # המרת הנתונים המפוענחים מ-JSON
    try:
        payload = json.loads(decrypted_vote)
        nonce = payload.get("nonce")
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing decrypted vote: {e}")
        return jsonify({"status": "error", "message": "Invalid decrypted vote format."}), 400

    if not nonce:
        return jsonify({"status": "error", "message": "Vote or nonce missing."}), 400

    # בדיקת ייחודיות ה-nonce
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM votes WHERE nonce = ?", (nonce,))
    nonce_count = cursor.fetchone()[0]
    conn.close()

    if nonce_count > 0:
        return jsonify({"status": "error", "message": "Duplicate vote detected."}), 400

    # שמירת ההצבעה בבסיס הנתונים
    add_encrypted_vote(encrypted_vote, center_id, nonce)
    
    # עדכון סטטוס המצביע
    mark_voter_as_voted(national_id)

    return jsonify({"status": "success", "message": "Vote submitted successfully!"})



@app.route('/zkp', methods=['POST'])
def handle_zkp():
    data = request.get_json()
    encrypted_graph = data.get("encryptedGraph")  # ה-SHA-256 שהגיע מהלקוח

    if not encrypted_graph:
        return jsonify({"status": "error", "message": "No encrypted graph provided."})

    # בדיקת התאמה מול בסיס הנתונים
    national_id, has_voted = get_voter_status_by_graph(encrypted_graph)

    if national_id is None:
        return jsonify({"status": "invalid", "message": "ID not recognized."})

    if has_voted:
        return jsonify({"status": "invalid", "message": "You have already voted!"})

    return jsonify({"status": "valid", "message": "ID can vote!"})


#### DH
# נקודת קצה לשליחת פרמטרי DH
@app.route('/dh/params', methods=['GET'])
def get_dh_params():
    return jsonify({
        "p": DH_PARAMS["p"],
        "g": DH_PARAMS["g"],
        "server_public_key": SERVER_PUBLIC_KEY
    })

@app.route('/dh/exchange', methods=['POST'])
def exchange_key():
    global SHARED_KEY
    data = request.get_json()
    client_public_key = data.get("client_public_key")
    if not client_public_key:
        return jsonify({"error": "No client public key provided."}), 400

    # חישוב המפתח המשותף
    SHARED_KEY = (int(client_public_key) ** SERVER_PRIVATE_KEY) % DH_PARAMS["p"]
    
    return jsonify({
        "shared_key_hash": sha256(str(SHARED_KEY).encode()).hexdigest()
    })

@app.route('/dh/verify', methods=['POST'])
def verify_key():
    global SHARED_KEY
    data = request.get_json()
    client_shared_key_hash = data.get("shared_key_hash")
    if not client_shared_key_hash:
        return jsonify({"error": "No shared key hash provided."}), 400
    print(client_shared_key_hash)
    # חישוב ה-Hash בצד השרת
    server_shared_key_hash = sha256(str(SHARED_KEY).encode()).hexdigest()
    print(server_shared_key_hash)
    if server_shared_key_hash == client_shared_key_hash:
        return jsonify({"status": "success", "message": "Shared key verified successfully!"})
    else:
        return jsonify({"status": "failure", "message": "Shared key does not match."})




#decrypt_votes
from hashlib import sha256
from cryptography.hazmat.primitives.padding import PKCS7

def remove_padding(data):
    """
    הסרת Padding מהנתונים המפוענחים
    """
    unpadder = PKCS7(128).unpadder()  # 128 ביט (16 בתים) מתאים ל-AES
    unpadded_data = unpadder.update(data) + unpadder.finalize()
    return unpadded_data


def get_aes_key_from_shared_key(shared_key):
    """
    יצירת מפתח AES תקין מ-shared_key באמצעות SHA256
    """
    shared_key_hash = sha256(str(shared_key).encode()).digest()
    return shared_key_hash[:32]  # החזר 32 בתים (256 ביט)

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64

def decrypt_vote(encrypted_vote, shared_key):
    """
    פענוח ההצבעה
    """
    try:
        # יצירת מפתח AES
        key_bytes = get_aes_key_from_shared_key(shared_key)
        encrypted_bytes = base64.b64decode(encrypted_vote)

        # יצירת צופן AES במצב ECB
        cipher = Cipher(algorithms.AES(key_bytes), modes.ECB())
        decryptor = cipher.decryptor()

        # פענוח הנתונים
        decrypted_bytes = decryptor.update(encrypted_bytes) + decryptor.finalize()

        # הסרת Padding
        decrypted_bytes = remove_padding(decrypted_bytes)

        # המרה למחרוזת
        decrypted_vote = decrypted_bytes.decode('utf-8')
        return decrypted_vote
    except UnicodeDecodeError as e:
        print(f"Error decoding decrypted bytes: {e}")
        return None
    except Exception as e:
        print(f"Error decrypting vote: {e}")
        return None



def generate_tally_hash(center_id, candidate, vote_count):
    """
    יוצר HASH לתוצאה מסוימת של מרכז ספירה.
    """
    payload = {
        "center_id": center_id,
        "candidate": candidate,
        "vote_count": vote_count,
    }
    payload_str = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()


#calc result
@app.route('/center_count_votes/<int:center_id>', methods=['POST'])
def center_count_votes(center_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # שליפת ההצבעות של המרכז
    cursor.execute("SELECT encrypted_vote, nonce, vote_hash FROM votes WHERE center_id = ?", (center_id,))
    votes = cursor.fetchall()

    results = {"Democratic": 0, "Republican": 0}
    seen_nonces = set()  # סט לבדיקת ייחודיות של nonce

    for encrypted_vote, nonce, vote_hash in votes:
        # בדיקת ייחודיות של nonce
        if nonce in seen_nonces:
            print(f"Duplicate nonce detected: {nonce}")
            continue
        seen_nonces.add(nonce)

        # פענוח ההצבעה
        decrypted_vote = decrypt_vote(encrypted_vote, SHARED_KEY)
        if not decrypted_vote:
            print(f"Failed to decrypt vote with nonce: {nonce}")
            continue

        # המרת ההצבעה מ-JSON
        payload = json.loads(decrypted_vote)
        vote = payload.get("vote")
        if not vote:
            print(f"Invalid vote payload: {payload}")
            continue

        # חישוב ה-HASH מחדש
        computed_hash = generate_vote_hash(encrypted_vote, nonce, center_id)

        # בדיקת התאמת ה-HASH
        if computed_hash != vote_hash:
            print(f"Hash mismatch detected for vote: {vote}, nonce: {nonce}")
            continue

        # עדכון תוצאות
        if vote in results:
            results[vote] += 1

    # מחיקת תוצאות קודמות של המרכז לפני שמירה מחדש
    cursor.execute("DELETE FROM tally_results WHERE center_id = ?", (center_id,))

    # שמירת התוצאות בטבלת tally_results
    for candidate, vote_count in results.items():
        result_hash = generate_tally_hash(center_id=center_id, candidate=candidate, vote_count=vote_count)
        cursor.execute(
            """
            INSERT INTO tally_results (center_id, candidate, vote_count, result_hash, timestamp)
            VALUES (?, ?, ?, ?, datetime('now'))
            """,
            (center_id, candidate, vote_count, result_hash)
        )

    conn.commit()
    conn.close()

    return jsonify({"center_id": center_id, "results": results})


@app.route('/total_count_votes', methods=['POST'])
def total_count_votes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # שליפת כל המועמדים והקולות מכל המרכזים
    cursor.execute("SELECT center_id, candidate, SUM(vote_count), result_hash FROM tally_results GROUP BY center_id, candidate")
    results = cursor.fetchall()

    final_results = {"Democratic": 0, "Republican": 0}

    for center_id, candidate, vote_count, result_hash in results:
        # חשב מחדש את ה-HASH
        computed_hash = generate_tally_hash(center_id=center_id, candidate=candidate, vote_count=vote_count)
        print("computed_hash:", computed_hash)
        print("result_hash:", result_hash)

        # בדוק אם ה-HASHים תואמים
        if computed_hash != result_hash:
            return jsonify({"error": f"Hash mismatch detected for center {center_id}"}), 400

        # הוסף את הקולות לתוצאה הסופית
        final_results[candidate] += vote_count

    conn.close()
    return jsonify(final_results)




#verify results

import hashlib
import json

def validate_all_hashes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT encrypted_vote, center_id, nonce, vote_hash FROM votes")
    votes = cursor.fetchall()

    for encrypted_vote, center_id, nonce, vote_hash in votes:
        decrypted_vote = decrypt_vote(encrypted_vote, SHARED_KEY)
        if not decrypted_vote:
            continue

        payload = json.loads(decrypted_vote)
        vote = payload.get("vote")
        computed_hash = generate_vote_hash(vote, nonce, center_id)
        if computed_hash != vote_hash:
            return False  # מצביע על שינוי במידע

    return True

def generate_vote_hash(vote, nonce, center_id):
    """
    יוצר hash ייחודי להצבעה
    """
    payload = {
        "vote": vote,
        "nonce": nonce,
        "center_id": center_id,
    }
    payload_str = json.dumps(payload, sort_keys=True)  # מחרוזת מסודרת ליציבות
    return hashlib.sha256(payload_str.encode()).hexdigest()


@app.route('/publish_results', methods=['GET'])
def publish_results():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # שליפת כל ההצבעות
    cursor.execute("SELECT encrypted_vote, center_id FROM votes")
    votes = cursor.fetchall()

    results = {"Democratic": 0, "Republican": 0}  # תוצאות סופיות
    center_results = {}  # תוצאות לפי מרכז
    vote_hashes = []

    for encrypted_vote, center_id in votes:
        # פענוח ההצבעה
        decrypted_vote = decrypt_vote(encrypted_vote, SHARED_KEY)
        if not decrypted_vote:
            print(f"Failed to decrypt vote from center {center_id}")
            continue

        # המרת ההצבעה ממחרוזת JSON
        payload = json.loads(decrypted_vote)
        vote = payload.get("vote")
        nonce = payload.get("nonce")

        # חישוב hash להצבעה
        computed_hash = generate_vote_hash(vote, nonce, center_id)
        vote_hashes.append({"hash": computed_hash, "center_id": center_id})

        # ספירת ההצבעות
        if vote in results:
            results[vote] += 1

        # ספירת תוצאות לפי מרכז
        if center_id not in center_results:
            center_results[center_id] = {"Democratic": 0, "Republican": 0}
        center_results[center_id][vote] += 1

    conn.close()

    return jsonify({
        "total_results": results,
        "center_results": center_results,
        "vote_hashes": vote_hashes,
    })



if __name__ == "__main__":
    app.run(debug=True)
