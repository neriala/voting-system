import networkx as nx
import random
import pickle
import socket

# פונקציה ליצירת גרף מתעודת זהות
def id_to_graph(id_number):
    random.seed(id_number)  # שימוש בת"ז כ-seed ליצירת גרף
    num_nodes = random.randint(5, 10)  # מספר צמתים אקראי
    edges = [(random.randint(0, num_nodes - 1), random.randint(0, num_nodes - 1)) for _ in range(num_nodes * 2)]
    graph = nx.Graph()
    graph.add_edges_from(edges)
    return graph

# יצירת גרף מתעודת זהות
client_id = "123456789"  # ת"ז של הלקוח
client_graph = id_to_graph(client_id)

# יצירת גרף מבלבל (permute)
permutation = list(client_graph.nodes)
random.shuffle(permutation)
obfuscated_graph = nx.relabel_nodes(client_graph, {i: permutation[i] for i in range(len(permutation))})

# שליחת הגרף לשרת וקבלת תשובה
def send_graph_to_server(obfuscated_graph, host='127.0.0.1', port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        data = pickle.dumps(obfuscated_graph)  # המרה לפורמט להעברה
        client_socket.sendall(data)
        response = client_socket.recv(1024).decode()
        print(f"תשובת השרת: {response}")

if __name__ == "__main__":
    send_graph_to_server(obfuscated_graph)
