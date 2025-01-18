# שרת: ניהול גרפים מתעודות זהות
import networkx as nx
import random
import pickle
import socket
import matplotlib.pyplot as plt

# פונקציה ליצירת גרף מתעודת זהות
def id_to_graph(id_number):
    random.seed(id_number)  # שימוש בת\"ז כ-seed ליצירת גרף
    num_nodes = random.randint(5, 10)  # מספר צמתים אקראי
    edges = [(random.randint(0, num_nodes - 1), random.randint(0, num_nodes - 1)) for _ in range(num_nodes * 2)]
    graph = nx.Graph()
    graph.add_edges_from(edges)
    return graph

# פונקציה לבדיקת איזומורפיזם בין שני גרפים
def is_isomorphic(graph1, graph2):
    return nx.is_isomorphic(graph1, graph2)

# יצירת מאגר גרפים מתעודות זהות
server_id_list = ["123456789", "987654321", "456123789"]  # רשימת ת\"ז לדוגמה
server_graphs = {id_num: id_to_graph(id_num) for id_num in server_id_list}

# פתיחת שרת והאזנה ללקוח
def run_server(host='127.0.0.1', port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"שרת מוכן להאזין בכתובת {host}:{port}")
        conn, addr = server_socket.accept()
        with conn:
            print(f"חיבור מ-{addr}")
            data = conn.recv(4096)
            if data:
                obfuscated_graph = pickle.loads(data)  # טעינת גרף מוסתר
                matching_graph = None
                for graph in server_graphs.values():
                    if is_isomorphic(obfuscated_graph, graph):
                        matching_graph = graph
                        break

                if matching_graph:
                    print("הגרף נמצא מתאים")
                    plt.figure("גרף הלקוח")
                    nx.draw(obfuscated_graph, with_labels=True)
                    plt.show()

                    plt.figure("גרף מתאים בשרת")
                    nx.draw(matching_graph, with_labels=True)
                    plt.show()

                    conn.sendall("הוכח".encode())
                else:
                    print("לא נמצא גרף מתאים")
                    conn.sendall("נכשל".encode())

if __name__ == "__main__":
    run_server()
