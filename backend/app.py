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

# משתנים לאחסון פרמטרי DH
DH_PARAMS = {"p": 8262525019121781265000801114122156349216670389155538325999152622344144720466698306297330225964244933192417628506609441718343308145224722902681373613370087, "g": 2}  # ערכים בסיסיים, ניתן להחליף באלו שמתאימים יותר
SERVER_PRIVATE_KEY = 4  # מפתח פרטי שרת
SERVER_PUBLIC_KEY = (DH_PARAMS["g"] ** SERVER_PRIVATE_KEY) % DH_PARAMS["p"]  # מפתח ציבורי שרת
SHARED_KEY = None


app = Flask(__name__)
CORS(app)  # אפשר תקשורת בין React ל-Flask

# נתיב מסד הנתונים
DB_PATH = r"C:\voting-system\DB\voting.db"

### פונקציות לניהול מסד הנתונים

def get_voter_status_by_graph(received_graph):
    """Checks if the graph matches any national ID in the database and returns voter status."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # שליפת כל הת"ז
    cursor.execute("SELECT national_id, has_voted FROM voters")
    voters = cursor.fetchall()
    conn.close()

    # בדיקת איזומורפיזם
    for national_id, has_voted in voters:
        graph = generate_graph_from_id(national_id)
        if nx.is_isomorphic(received_graph, graph):
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
    שמירת ההצבעה המוצפנת בבסיס הנתונים יחד עם nonce ייחודי.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO votes (encrypted_vote, center_id, nonce) VALUES (?, ?, ?)",
        (encrypted_vote, center_id, nonce),
    )
    conn.commit()
    conn.close()




### פונקציות ליצירת גרפים

def generate_graph_from_id(id_number):
    """Generates a graph from a national ID."""
    graph = nx.Graph()
    edges = [
        (int(id_number[i]), int(id_number[j]))
        for i in range(8)
        for j in range(i + 1, 9)
        if (int(id_number[i]) + int(id_number[j])) % 3 == 0
    ]
    graph.add_edges_from(edges)
    return graph

### נקודות קצה (Endpoints)
@app.route('/vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    graph_data = data.get("graph")
    encrypted_vote = data.get("encrypted_vote")
    center_id = data.get("center_id")

    if not graph_data or not encrypted_vote or not center_id:
        return jsonify({"status": "error", "message": "Missing data."}), 400

    # יצירת הגרף מהמידע
    received_graph = nx.Graph()
    received_graph.add_nodes_from(graph_data["nodes"])
    received_graph.add_edges_from(graph_data["edges"])
    print("Received encrypted vote:", encrypted_vote)

    # בדיקת איזומורפיזם מול בסיס הנתונים
    national_id, has_voted = get_voter_status_by_graph(received_graph)
    if national_id is None:
        return jsonify({"status": "invalid", "message": "ID not recognized."})
    if has_voted:
        return jsonify({"status": "invalid", "message": "Already voted."})

    print(f"Shared Key on server: {SHARED_KEY}")

    # פענוח ההצבעה
    decrypted_vote = decrypt_vote(encrypted_vote, SHARED_KEY)
    if not decrypted_vote:
        return jsonify({"status": "error", "message": "Failed to decrypt vote."}), 500

    # המרת הנתונים המפוענחים מ-JSON
    try:
        payload = json.loads(decrypted_vote)
        vote = payload.get("vote")
        nonce = payload.get("nonce")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing decrypted vote: {e}")
        return jsonify({"status": "error", "message": "Invalid decrypted vote format."}), 400

    if not vote or not nonce:
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
    print(f"###########Add {center_id}#######")
    # עדכון סטטוס המצביע
    mark_voter_as_voted(national_id)

    return jsonify({"status": "success", "message": "Vote submitted successfully!"})


@app.route('/zkp', methods=['POST'])
def handle_zkp():
    data = request.get_json()
    print(data)
    graph_data = data.get("graph")
    encrypted_vote = data.get("encrypted_vote")
    center_id = data.get("center_id")

    if not graph_data:
        return jsonify({"status": "error", "message": "No graph data provided."})

    # המרת המידע לגרף NetworkX
    received_graph = nx.Graph()
    received_graph.add_nodes_from(graph_data["nodes"])
    received_graph.add_edges_from(graph_data["edges"])

    # בדיקת איזומורפיזם מול בסיס הנתונים
    national_id, has_voted = get_voter_status_by_graph(received_graph)
    if national_id is None:
        return jsonify({"status": "invalid", "message": "ID not recognized."})

    if has_voted:
        return jsonify({"status": "invalid", "message": "You have already voted!"})

    # עדכון מסד הנתונים
    #mark_voter_as_voted(national_id)
    #add_encrypted_vote(encrypted_vote, center_id)
    
    return jsonify({"status": "valid", "message": "ID can voted!!"})


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
        print(f"Decrypted raw bytes (unpadded): {decrypted_bytes}")

        # המרה למחרוזת
        decrypted_vote = decrypted_bytes.decode('utf-8')
        return decrypted_vote
    except UnicodeDecodeError as e:
        print(f"Error decoding decrypted bytes: {e}")
        return None
    except Exception as e:
        print(f"Error decrypting vote: {e}")
        return None






#calc result
@app.route('/center_count_votes/<int:center_id>', methods=['POST'])
def center_count_votes(center_id):
    print(f"Center ID:{center_id}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # שליפת ההצבעות של מרכז הספירה הספציפי
    cursor.execute("SELECT encrypted_vote FROM votes WHERE center_id = ?", (center_id,))
    votes = cursor.fetchall()
    print(votes)
    results = {"Democratic": 0, "Republican": 0}

    for (encrypted_vote,) in votes:
        decrypted_vote = decrypt_vote(encrypted_vote, SHARED_KEY)
        if not decrypted_vote:
            continue

        payload = json.loads(decrypted_vote)
        vote = payload.get("vote")

        if vote in results:
            results[vote] += 1
    print(results)
    conn.close()
    return jsonify({"center_id": center_id, "results": results})

@app.route('/total_count_votes', methods=['POST'])
def total_count_votes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT center_id FROM votes")
    centers = cursor.fetchall()

    total_results = {"Democratic": 0, "Republican": 0}

    for (center_id,) in centers:
        response = center_count_votes(center_id).get_json()
        center_results = response["results"]

        for candidate, count in center_results.items():
            total_results[candidate] += count

    conn.close()
    return jsonify(total_results)




if __name__ == "__main__":
    app.run(debug=True)
