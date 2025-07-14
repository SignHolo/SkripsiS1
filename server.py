import socket
import threading

HOST = '0.0.0.0'# localhost
PORT = 12345

clients = {}  # Store connected clients by name

def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")

    name = conn.recv(1024).decode().strip()
    if name not in ["opencv", "esp"]:
        print(f"[ERROR] Unknown client type: {name}")
        conn.close()
        return

    clients[name] = conn
    print(f"[INFO] Registered {name} client.")

    if name == "opencv":
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"[DATA from OpenCV]: {data.decode().strip()}")

                # Forward to ESP if connected
                if "esp" in clients:
                    try:
                        clients["esp"].sendall(data)
                    except:
                        print("[WARN] Failed to send to ESP.")
            except:
                break

    elif name == "esp":
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"[ESP SENT DATA]: {data.decode().strip()}")
                # If you expect ESP to send something back
            except:
                break

    print(f"[DISCONNECTED] {name}")
    if name in clients:
        del clients[name]
    conn.close()

# === Main Server Loop ===
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)
print(f"[TCP Server] Listening on {HOST}:{PORT}")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
