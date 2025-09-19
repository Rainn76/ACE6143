import socket, sys, time, hashlib, base64

MAX_RETRIES = 3  # max retransmissions

def encrypt(msg, key="ace6143"):
    """Simple XOR encryption"""
    encrypted = bytearray()
    for i, c in enumerate(msg):
        encrypted.append(ord(c) ^ ord(key[i % len(key)]))
    return base64.b64encode(encrypted).decode()

def decrypt(encrypted_msg, key="ace6143"):
    """Simple XOR decryption"""
    try:
        data = base64.b64decode(encrypted_msg)
        return ''.join(chr(b ^ ord(key[i % len(key)])) for i, b in enumerate(data))
    except:
        return encrypted_msg

def checksum(data):
    """Calculate MD5 checksum (first 8 chars)"""
    return hashlib.md5(data.encode()).hexdigest()[:8]

def connect_socket(protocol):
    """Create and connect socket with retry"""
    hostname, port = "localhost", 28000
    for attempt in range(3):
        try:
            sock_type = socket.SOCK_STREAM if protocol == "tcp" else socket.SOCK_DGRAM
            s = socket.socket(socket.AF_INET, sock_type)
            s.settimeout(5)
            
            if protocol == "tcp":
                s.connect((hostname, port))
                print(f"[TCP] Connected to {hostname}:{port}")
            else:
                print(f"[UDP] Ready to send to {hostname}:{port}")
            
            return s
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(1)
    return None

def send_and_receive(s, protocol, send_data, hostname, port):
    """Send data and handle retransmission"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if protocol == "tcp":
                s.send(send_data.encode())
                reply = s.recv(1024).decode()
            else:
                s.sendto(send_data.encode(), (hostname, port))
                reply, _ = s.recvfrom(1024)
                reply = reply.decode()

            # Check for corruption
            if checksum(reply) != checksum(send_data):
                print(f"[WARN] Corrupted packet (attempt {attempt}), retransmitting...")
                continue

            return reply  # success

        except socket.timeout:
            print(f"[WARN] Timeout (attempt {attempt}), retransmitting...")
            continue

    print("[ERROR] Retries exceeded. Message failed.")
    return None

def main():
    protocol = input("Protocol (tcp/udp): ").lower().strip()
    encrypt_enable = input("Enable encryption (y/n): ").lower().strip() == 'y'

    s = connect_socket(protocol)
    if not s:
        sys.exit(1)

    print("Type messages (ctrl+c to quit):")
    print("-" * 30)

    stats = {'sent': 0, 'received': 0, 'total_time': 0}
    hostname, port = "localhost", 28000

    try:
        while True:
            msg = input("> ").strip()
            if not msg:
                continue
                
            start_time = time.time()
            stats['sent'] += 1
            
            # Prepare message
            send_data = encrypt(msg) if encrypt_enable else msg
            out_checksum = checksum(send_data)
            print(f"[SEND] Checksum: {out_checksum}")
            if encrypt_enable:
                print(f"[ENCRYPT] Message encrypted")

            reply = send_and_receive(s, protocol, send_data, hostname, port)
            if reply is None:
                continue  # skip if retries failed

            # Process response
            rtt = (time.time() - start_time) * 1000
            stats['received'] += 1
            stats['total_time'] += rtt
            
            final_reply = decrypt(reply) if encrypt_enable else reply
            reply_checksum = checksum(reply)
            
            print(f"[RECV] {final_reply.strip()}")
            print(f"[RECV] Checksum: {reply_checksum}")
            print(f"[TIME] RTT: {rtt:.1f}ms")
                
    except KeyboardInterrupt:
        print("\n[INFO] Disconnecting...")

    finally:
        if s:
            s.close()
        
        # Print stats
        print(f"\nStats: Sent={stats['sent']}, Received={stats['received']}")
        if stats['received'] > 0:
            avg_rtt = stats['total_time'] / stats['received']
            success_rate = (stats['received'] / stats['sent']) * 100
            print(f"Success Rate: {success_rate:.1f}%, Avg RTT: {avg_rtt:.1f}ms")

if __name__ == "__main__":
    main()
