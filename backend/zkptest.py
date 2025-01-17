import networkx as nx
import hashlib

# פונקציה להצפנת ת"ז
def hash_id(national_id):
    return hashlib.sha256(national_id.encode()).hexdigest()

# רשימת ת"ז של מצביעים
voters_ids = ["123456789", "987654321", "111222333", "444555666"]

# גרף השרת
server_graph = nx.Graph()
hashed_ids = [hash_id(voter_id) for voter_id in voters_ids]
server_graph.add_edges_from([
    (hashed_ids[0], hashed_ids[1]),
    (hashed_ids[1], hashed_ids[2]),
    (hashed_ids[2], hashed_ids[3]),
    (hashed_ids[3], hashed_ids[0])
])
# אימות ההוכחה בשרת
def verify_proof(proof, graph):
    node = proof["node"]
    neighbors = proof["neighbors"]
    return set(neighbors) == set(graph.neighbors(node))

# בדיקת ההוכחה


if __name__ == '__main__':

    print("Server graph nodes:", server_graph.nodes)

    # המצביע מחזיק רק את הת"ז שלו
    voter_id = "123456789"
    hashed_voter_id = hash_id(voter_id)

    # המצביע מקבל את השכנים שלו (חתיכה מהגרף)
    def get_neighbors(node, graph):
        return list(graph.neighbors(node))

    # דוגמה לשכנים של המצביע
    voter_neighbors = get_neighbors(hashed_voter_id, server_graph)
    print("Voter neighbors:", voter_neighbors)

    # המצביע שולח את ההוכחה
    proof = {"node": hashed_voter_id, "neighbors": voter_neighbors}

    is_valid = verify_proof(proof, server_graph)
    print("Is the proof valid?", is_valid)
