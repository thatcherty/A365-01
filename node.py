import socket       # open sockets for client server communication
import threading    # allow a node to be both a client and server
import time
import selectors    # allow a server to serve multiple clients
import types        # obj for addr and data from listening port
from dataclasses import dataclass, field
from typing import ClassVar
import sys

LISTENING_PORT = 65432

LOOKUP = {
    b"SEA": "127.0.0.1",
    b"ANC": "127.0.0.2",
    b"FAI": "127.0.0.3",
    b"JNU": "127.0.0.4",
    b"SIT": "127.0.0.5",
    b"ADK": "127.0.0.6",
    b"ADQ": "127.0.0.7",
    b"OTZ": "127.0.0.8",
    b"NME": "127.0.0.9",
    b"BET": "127.0.0.10",
    b"AKN": "127.0.0.11",
    b"DLG": "127.0.0.12",
    b"BRW": "127.0.0.13",
    b"SCC": "127.0.0.14",
    b"CDV": "127.0.0.15",
    b"DUT": "127.0.0.16",
    b"KTN": "127.0.0.17",
}

HUBS = [b"ANC", b"SEA"]

airports: list[node] = []
airport_threads = []
airport_index = {}

@dataclass
class node:
    index : ClassVar[int] = 0
    name: str
    host : str
    server_port : int
    hub : bool
    listening_socket : socket = field(default=False, init=False)

    def __post_init__(self):
        type(self).index += 1

    def start_server(self):

        def accept_wrapper(sock):
            conn, addr = sock.accept()
            print(f"{self.name} accepted connection from {addr}")
            conn.setblocking(False)
            data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
            sel.register(conn, events, data=data)

        def service_connection(key, mask):
            sock = key.fileobj
            data = key.data
            if mask & selectors.EVENT_READ:
                recv_data = sock.recv(1024)
                if recv_data:
                    data.outb += recv_data

                else:
                    print(f"Closing connection to {data.addr}")
                    sel.unregister(sock)
                    sock.close()
            
            if mask & selectors.EVENT_WRITE:
                if data.outb:
                    dest = data.outb[5:8]
                    origin = data.outb[0:3]
                    passenger = data.outb[10:]
                    print(f"{self.name} echoing {data.outb!r} to {data.addr}")
                    sent = sock.send(data.outb)
                    data.outb = data.outb[sent:]

                    if dest != self.name:
                        print(f"Sending {passenger} from {self.name!r} @ {LOOKUP[origin]} to {dest} @ {LOOKUP[dest]}")
                        temp_client = threading.Thread(target=self.start_client, args=(dest, LISTENING_PORT,), kwargs={"data": data.outb})
                        temp_client.start()


        print(f"Starting server on {self.host} listening on port {self.server_port}")
        sel = selectors.DefaultSelector()

        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening_socket.bind((self.host, self.server_port))
        self.listening_socket.listen()
        self.listening_socket.setblocking(False)
        sel.register(self.listening_socket, selectors.EVENT_READ, data=None)

        try:
            while True:
                events = sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        accept_wrapper(key.fileobj)
                    else:
                        service_connection(key,mask)
        except KeyboardInterrupt:
            print("Exiting - keyboard interrupt")

        finally:
            sel.close()


    def start_client(self, dest_host, dest_port, data):
        print(f"Starting client on {self.host}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((LOOKUP[self.name],0))
        sock.connect((LOOKUP[dest_host], dest_port))
        sock.sendall(data)
        response = sock.recv(1024)
        print(f"{self.name} got response {response} from {dest_host} on port {dest_port}")
        sock.close()

    def initialize(self):
        print(f"Initializing {self.name}")
        server = threading.Thread(target=self.start_server)
        server.start()

@dataclass
class manager:

    payload : str = ""
    origin = b""
    #ip = "127.0.0.18"

    def run(self):
        self.collect_payload()
        self.start_client()

    def collect_payload(self):
        self.payload = input("Please enter your origin:\n")
        self.origin = self.payload.strip().encode("utf-8")
        print(self.origin)
        print(LOOKUP[self.origin])
        self.payload = self.payload + ", " + input("Please enter your destination:\n")
        self.payload = self.payload + ", " + input("Please enter your name:\n")

    def start_client(self):
        print(f"Starting air traffic manager")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.18", 0))
        sock.connect((LOOKUP[self.origin], LISTENING_PORT))
        sock.sendall(self.payload.encode("utf-8"))
        response = sock.recv(1024)
        print(f"Air traffic manager got response {response} from {self.origin} on port {LISTENING_PORT}")
        self.payload = ""
        self.origin = b""
        sock.close()


if __name__ == "__main__":

    for name, ip in LOOKUP.items():
        temp = node(name, ip, LISTENING_PORT, True if name in HUBS else False)
        t = threading.Thread(target=temp.start_server)
        airports.append(temp)
        airport_threads.append(t)
        airport_index[name] = node.index

    for t in airport_threads:
        t.start()

    for airport in airports:
        print(airport.name)
        print(airport.listening_socket.getsockname())

    print(node.index)

    airport_manager = manager()
    user_in = ""

    while True:
        airport_manager.run()
        user_in = input("Type exit to leave or press enter to input more:\n")

        if user_in.lower() == "exit":
            # any necessary cleanup of sockets
            # exit program
            # sys.exit() does not work
            pass
        else:
            continue



