import sqlite3
import networkx as nx
import base64
import json
import hashlib
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from hashlib import sha256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.padding import PKCS7




#DH PAR
DH_PARAMS = {"p": 8262525019121781265000801114122156349216670389155538325999152622344144720466698306297330225964244933192417628506609441718343308145224722902681373613370087, "g": 2}  # ערכים בסיסיים, ניתן להחליף באלו שמתאימים יותר
SERVER_PRIVATE_KEY = 4  
SERVER_PUBLIC_KEY = (DH_PARAMS["g"] ** SERVER_PRIVATE_KEY) % DH_PARAMS["p"]  
SHARED_KEY = None


app = Flask(__name__)
CORS(app)  

# DB PATH
DB_PATH = r"C:\voting-system\DB\voting.db"



def get_voter_status_by_graph(received_encrypted_graph):
    """Checks if the encrypted graph matches any hashed national ID in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT national_id, has_voted FROM voters")
    voters = cursor.fetchall()
    conn.close()

    for national_id, has_voted in voters:
        database_graph = generate_graph_from_id(national_id)
        
        database_encrypted_graph = compute_sha256(database_graph)
        #print(f"Received Encrypted Graph: {received_encrypted_graph}")
        #print(f"Database Encrypted Graph: {database_encrypted_graph}")

        if received_encrypted_graph == database_encrypted_graph:
            #print(f"Match found for ID {national_id}. Voted: {has_voted}")
            return national_id, has_voted

    return None, None


def mark_voter_as_voted(national_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE voters SET has_voted = 1 WHERE national_id = ?", (national_id,))
    conn.commit()
    conn.close()


def add_encrypted_vote(encrypted_vote, center_id, nonce):
    vote_hash = generate_vote_hash(encrypted_vote, nonce, center_id)  
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO votes (encrypted_vote, center_id, nonce, vote_hash) VALUES (?, ?, ?, ?)",
        (encrypted_vote, center_id, nonce, vote_hash),
    )
    conn.commit()
    conn.close()


def generate_graph_from_id(id_number):
    graph = {"nodes": [], "edges": []}

    nodes = list(set(int(char) for char in id_number))
    graph["nodes"] = nodes

    edges = []
    for i in range(len(id_number) - 1):
        edge = (int(id_number[i]), int(id_number[i + 1]))
        edges.append(edge)
    graph["edges"] = edges

    return graph


def compute_sha256(graph):
    graph["edges"] = [list(edge) for edge in graph["edges"]]

    graph_string = json.dumps(graph, separators=(",", ":"))
    return hashlib.sha256(graph_string.encode()).hexdigest()



######### submit VOTE #########
@app.route('/vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    graph_data = data.get("encryptedGraph")
    encrypted_vote = data.get("encrypted_vote")
    center_id = data.get("center_id")
    if not graph_data or not encrypted_vote or not center_id:
        return jsonify({"status": "error", "message": "Missing data."}), 400

    national_id, has_voted = get_voter_status_by_graph(graph_data)

    decrypted_vote = decrypt_vote(encrypted_vote, SHARED_KEY)

    if not decrypted_vote:
        return jsonify({"status": "error", "message": "Failed to decrypt vote."}), 500

    try:
        payload = json.loads(decrypted_vote)
        nonce = payload.get("nonce")
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing decrypted vote: {e}")
        return jsonify({"status": "error", "message": "Invalid decrypted vote format."}), 400

    if not nonce:
        return jsonify({"status": "error", "message": "Vote or nonce missing."}), 400

    #check nonce unique
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM votes WHERE nonce = ?", (nonce,))
    nonce_count = cursor.fetchone()[0]
    conn.close()

    if nonce_count > 0:
        return jsonify({"status": "error", "message": "Duplicate vote detected."}), 400

    add_encrypted_vote(encrypted_vote, center_id, nonce)
    mark_voter_as_voted(national_id)

    return jsonify({"status": "success", "message": "Vote submitted successfully!"})

def remove_padding(data):
    unpadder = PKCS7(128).unpadder() 
    unpadded_data = unpadder.update(data) + unpadder.finalize()
    return unpadded_data


def get_aes_key_from_shared_key(shared_key):
    shared_key_hash = sha256(str(shared_key).encode()).digest()
    return shared_key_hash[:32]  



def decrypt_vote(encrypted_vote, shared_key):
    try:
        # create aes key
        key_bytes = get_aes_key_from_shared_key(shared_key)
        encrypted_bytes = base64.b64decode(encrypted_vote)

        # cipher ecb mode
        cipher = Cipher(algorithms.AES(key_bytes), modes.ECB())
        decryptor = cipher.decryptor()

        # decrypt
        decrypted_bytes = decryptor.update(encrypted_bytes) + decryptor.finalize()

        # remove Padding
        decrypted_bytes = remove_padding(decrypted_bytes)

        # to string
        decrypted_vote = decrypted_bytes.decode('utf-8')
        return decrypted_vote

    except UnicodeDecodeError as e:
        print(f"Error decoding decrypted bytes: {e}")
        return None
    except Exception as e:
        print(f"Error decrypting vote: {e}")
        return None


######### ZKP #########
@app.route('/zkp', methods=['POST'])
def handle_zkp():
    data = request.get_json()
    encrypted_graph = data.get("encryptedGraph") 

    if not encrypted_graph:
        return jsonify({"status": "error", "message": "No encrypted graph provided."})

    national_id, has_voted = get_voter_status_by_graph(encrypted_graph)

    if national_id is None:
        return jsonify({"status": "invalid", "message": "ID not recognized."})

    if has_voted:
        return jsonify({"status": "invalid", "message": "You have already voted!"})

    return jsonify({"status": "valid", "message": "ID can vote!"})


######### DH #########
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

    server_shared_key_hash = sha256(str(SHARED_KEY).encode()).hexdigest()
    if server_shared_key_hash == client_shared_key_hash:
        return jsonify({"status": "success", "message": "Shared key verified successfully!"})
    else:
        return jsonify({"status": "failure", "message": "Shared key does not match."})




######### Calc Result #########
@app.route('/center_count_votes/<int:center_id>', methods=['POST'])
def center_count_votes(center_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT encrypted_vote, nonce, vote_hash FROM votes WHERE center_id = ?", (center_id,))
    votes = cursor.fetchall()

    results = {"Democratic": 0, "Republican": 0}
    seen_nonces = set()  

    for encrypted_vote, nonce, vote_hash in votes:
        if nonce in seen_nonces:
            print(f"Duplicate nonce detected: {nonce}")
            continue
        seen_nonces.add(nonce)

        decrypted_vote = decrypt_vote(encrypted_vote, SHARED_KEY)
        if not decrypted_vote:
            print(f"Failed to decrypt vote with nonce: {nonce}")
            continue

        payload = json.loads(decrypted_vote)
        vote = payload.get("vote")
        if not vote:
            print(f"Invalid vote payload: {payload}")
            continue

        # calc hash to check fake
        computed_hash = generate_vote_hash(encrypted_vote, nonce, center_id)
        if computed_hash != vote_hash:
            print(f"Hash mismatch detected for vote: {vote}, nonce: {nonce}")
            continue

        if vote in results:
            results[vote] += 1

    # for case if we have last calc in table. delete and add new
    cursor.execute("DELETE FROM tally_results WHERE center_id = ?", (center_id,))

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

    cursor.execute("SELECT center_id, candidate, SUM(vote_count), result_hash FROM tally_results GROUP BY center_id, candidate")
    results = cursor.fetchall()

    final_results = {"Democratic": 0, "Republican": 0}

    for center_id, candidate, vote_count, result_hash in results:
        computed_hash = generate_tally_hash(center_id=center_id, candidate=candidate, vote_count=vote_count)
        if computed_hash != result_hash:
            return jsonify({"error": f"Hash mismatch detected for center {center_id}"}), 400

        final_results[candidate] += vote_count

    conn.close()
    return jsonify(final_results)



def generate_tally_hash(center_id, candidate, vote_count):
    payload = {
        "center_id": center_id,
        "candidate": candidate,
        "vote_count": vote_count,
    }
    payload_str = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()

def generate_vote_hash(vote, nonce, center_id):
    payload = {
        "vote": vote,
        "nonce": nonce,
        "center_id": center_id,
    }
    payload_str = json.dumps(payload, sort_keys=True) 
    return hashlib.sha256(payload_str.encode()).hexdigest()

######### verify #########
@app.route('/publish_results', methods=['GET'])
def publish_results():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT encrypted_vote, center_id FROM votes")
    votes = cursor.fetchall()

    results = {"Democratic": 0, "Republican": 0} #total result
    center_results = {}  #by center
    vote_hashes = []

    for encrypted_vote, center_id in votes:
        decrypted_vote = decrypt_vote(encrypted_vote, SHARED_KEY)
        if not decrypted_vote:
            print(f"Failed to decrypt vote from center {center_id}")
            continue

        payload = json.loads(decrypted_vote)
        vote = payload.get("vote")
        nonce = payload.get("nonce")

        computed_hash = generate_vote_hash(vote, nonce, center_id)
        vote_hashes.append({"hash": computed_hash, "center_id": center_id})

        if vote in results:
            results[vote] += 1

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
