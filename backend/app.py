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

def add_encrypted_vote(encrypted_vote, center_id):
    """Adds an encrypted vote to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO votes (encrypted_vote, center_id) VALUES (?, ?)",
        (encrypted_vote, center_id),
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
    print(encrypted_vote)
    # בדיקת איזומורפיזם מול בסיס הנתונים
    national_id, has_voted = get_voter_status_by_graph(received_graph)
    if national_id is None:
        return jsonify({"status": "invalid", "message": "ID not recognized."})
    if has_voted:
        return jsonify({"status": "invalid", "message": "Already voted."})
    print("SHARED_KEY")
    print(SHARED_KEY)
    decrypted_vote = decrypt_vote(encrypted_vote, SHARED_KEY)
    
    #decrypted_vote=None
    if not decrypted_vote:
        return jsonify({"status": "error", "message": "Failed to decrypt vote."}), 500

    print(f"Decrypted vote: {decrypted_vote}")  # הדפסת הבחירה (לדיבוג)

    # עדכון סטטוס ושמירת ההצבעה
    mark_voter_as_voted(national_id)
    add_encrypted_vote(encrypted_vote, center_id)
    
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
    print("EXHANC")
    print(SHARED_KEY)
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
    פונקציה לפענוח ההצבעה
    :param encrypted_vote: ההצבעה המוצפנת (מחרוזת)
    :param shared_key: המפתח המשותף (שלם)
    :return: תוכן הפענוח (הבחירה)
    """
    try:
        # יצירת מפתח AES
        key_bytes = get_aes_key_from_shared_key(shared_key)
        
        print(f"Generated AES Key (server, Hex): {key_bytes.hex()}")

        # ההצבעה המוצפנת מגיעה בקידוד Base64
        encrypted_bytes = base64.b64decode(encrypted_vote)

        # יצירת צופן AES במצב ECB עם Pkcs7 padding
        cipher = Cipher(algorithms.AES(key_bytes), modes.ECB())
        decryptor = cipher.decryptor()

        # פענוח הנתונים
        decrypted_bytes = decryptor.update(encrypted_bytes) + decryptor.finalize()

        # הדפסת הבתים הגולמיים לצורך דיבוג
        print(f"Decrypted raw bytes: {decrypted_bytes}")

        # נסה להמיר למחרוזת UTF-8
        decrypted_vote = decrypted_bytes.decode('utf-8')
        return decrypted_vote
    except UnicodeDecodeError as e:
        print(f"Error decoding decrypted bytes: {e}")
        return None
    except Exception as e:
        print(f"Error decrypting vote: {e}")
        return None


if __name__ == "__main__":
    app.run(debug=True)
