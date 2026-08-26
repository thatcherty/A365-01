import socket

ANC = "127.0.0.1"
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((ANC,PORT))
    s.sendall(b"Hello, Anchorage!")
    data = s.recv(1024)

print(f"Received {data!r}")

