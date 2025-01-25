from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import networkx as nx

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
    cursor.execute("INSERT INTO votes (encrypted_vote, center_id) VALUES (?, ?)", (encrypted_vote, center_id))
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

if __name__ == "__main__":
    app.run(debug=True)
