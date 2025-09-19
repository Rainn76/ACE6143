# ------------ Modules -----------
import socket, threading, logging
from datetime import datetime

# ------------ Config ------------
HOST, PORT = "localhost", 28000
MAX_MSG = 1024
IDLE_TIMEOUT = 60   # seconds
LOG_FILE = "server.log"

# ------------ Logging ------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
clients = {}
lock = threading.Lock()

# ------------ TCP Client Handler ------------
def handle_tcp(conn, addr):
    addr_str = f"{addr[0]}:{addr[1]}"
    with lock: clients[conn] = datetime.now()
    logging.info(f"[TCP] Connected {addr_str}")

    try:
        while True:
            conn.settimeout(1)
            try:
                data = conn.recv(MAX_MSG)
            except socket.timeout:
                with lock:
                    last = clients.get(conn, datetime.now())
                if (datetime.now() - last).seconds > IDLE_TIMEOUT:
                    logging.info(f"[TCP] Kicked {addr_str} (idle)")
                    break
                continue
            if not data: break
            with lock: clients[conn] = datetime.now()
            msg = data.decode(errors="ignore").strip()
            logging.info(f"[TCP] {addr_str} -> {msg}")
            conn.sendall(data)  # echo
    finally:
        with lock: clients.pop(conn, None)
        conn.close()
        logging.info(f"[TCP] Disconnected {addr_str}")

# ------------ TCP Server ------------
def tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        logging.info(f"[TCP] Listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_tcp, args=(conn, addr), daemon=True).start()

# ------------ UDP Server ------------
def udp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        logging.info(f"[UDP] Listening on {HOST}:{PORT}")
        while True:
            data, addr = s.recvfrom(MAX_MSG)
            msg = data.decode(errors="ignore").strip()
            logging.info(f"[UDP] {addr} -> {msg}")
            s.sendto(data, addr)  # echo

# ------------ Main ------------
if __name__ == "__main__":
    threading.Thread(target=tcp_server, daemon=True).start()
    threading.Thread(target=udp_server, daemon=True).start()
    logging.info("Server running (TCP + UDP)")
    try:
        while True: pass  # keep alive
    except KeyboardInterrupt:
        logging.info("Server shutting down...")