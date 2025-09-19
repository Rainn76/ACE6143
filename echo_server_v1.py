import socket, threading, logging, random, time

# ------------ Config ------------
HOST, PORT = "localhost", 28000
MAX_MSG = 1024
LOSS_PROB = 0.25       # 20% chance to drop packets
DELAY_PROB = 0.25     # 20% chance to delay packets
CORRUPT_PROB = 0.30    # 10% chance to corrupt packets
MAX_DELAY = 2.0       # max delay in seconds

# ------------ Logging ------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ------------ TCP Handler ------------
def handle_tcp(conn, addr):
    addr_str = f"{addr[0]}:{addr[1]}"
    logging.info(f"[TCP] Connected {addr_str}")
    try:
        while True:
            data = conn.recv(MAX_MSG)
            if not data:
                break
            msg = data.decode(errors="ignore").strip()
            logging.info(f"[TCP] {addr_str} -> {msg}")

            # --- Simulate network issues ---
            if random.random() < LOSS_PROB:
                logging.warning(f"[TCP] Dropped packet from {addr_str}")
                continue
            if random.random() < DELAY_PROB:
                d = random.uniform(0.5, MAX_DELAY)
                logging.warning(f"[TCP] Delaying {d:.1f}s packet from {addr_str}")
                time.sleep(d)
            if random.random() < CORRUPT_PROB:
                corrupted = bytearray(data)
                corrupted[random.randrange(len(corrupted))] ^= 0x01
                data = bytes(corrupted)
                logging.warning(f"[TCP] Corrupted packet from {addr_str}")

            conn.sendall(data)
    finally:
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

            # --- Simulate network issues ---
            if random.random() < LOSS_PROB:
                logging.warning(f"[UDP] Dropped packet from {addr}")
                continue
            if random.random() < DELAY_PROB:
                d = random.uniform(0.5, MAX_DELAY)
                logging.warning(f"[UDP] Delaying {d:.1f}s packet from {addr}")
                time.sleep(d)
            if random.random() < CORRUPT_PROB:
                corrupted = bytearray(data)
                corrupted[random.randrange(len(corrupted))] ^= 0x01
                data = bytes(corrupted)
                logging.warning(f"[UDP] Corrupted packet from {addr}")

            s.sendto(data, addr)

# ------------ Main ------------
if __name__ == "__main__":
    threading.Thread(target=tcp_server, daemon=True).start()
    threading.Thread(target=udp_server, daemon=True).start()
    logging.info("Special Echo Server running with simulated packet loss/delay/corruption")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Server shutting down...")
