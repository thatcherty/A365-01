import socket       # open sockets for client server communication
import threading    # allow a node to be both a client and server
import time
import selectors    # allow a server to serve multiple clients
import types        # obj for addr and data from listening port
from dataclasses import dataclass, field
from typing import ClassVar
import sys
import logging
from pathlib import Path

LOG = 1
logging.basicConfig(filename=Path(__file__).with_name("air_traffic.log"), filemode="w", level=logging.INFO, format="%(asctime)s [%(threadName)s] %(message)s")
logger = logging.getLogger("air_traffic")

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

DIRECT = [
    # SEA ANC FAI JNU SIT ADK ADQ OTZ NME BET AKN DLG BRW SCC CDV DUT KTN

    [0,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1],  # SEA
    [1,  0,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1],  # ANC

    [0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # FAI -> ANC
    [1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # JNU -> SEA
    [1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # SIT -> SEA/ANC
    [0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # ADK -> ANC
    [1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # ADQ -> SEA/ANC
    [0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # OTZ -> ANC
    [0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # NME -> ANC
    [1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # BET -> SEA/ANC
    [0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # AKN -> ANC
    [1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # DLG -> SEA/ANC
    [0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # BRW -> ANC
    [0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # SCC -> ANC
    [1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # CDV -> SEA/ANC
    [1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # DUT -> SEA
    [1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],  # KTN -> SEA
]

# General format - DIRECT[origin][destination]
# Identify if layover required  if DIRECT[airport_index[origin]][airport_index[destination]] = 0
# Identify which hub origin can fly to
# DIRECT[airport_index[origin]][1] -> ANC
# DIRECT[airport_index[origin]][0] -> SEA
# Hubs always check destination to confirm whether they are a layover or a destination

HUBS = [b"SEA", b"ANC"]

airports = []
airport_threads = []
airport_index = {}

@dataclass
class node:
    index : ClassVar[int] = 0
    name: str
    host : str
    server_port : int
    hub : bool
    listening_socket: socket.socket = field(default=None, init=False)
    ready: threading.Event = field(default_factory=threading.Event, init=False)

    def __post_init__(self):
        type(self).index += 1

    def start_server(self):
        sel = selectors.DefaultSelector()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                self.listening_socket = server
                server.bind((self.host, self.server_port))
                server.listen()
                server.setblocking(False)
                sel.register(server, selectors.EVENT_READ)
                logger.info("%s listening at %s:%s", self.name.decode(), self.host, self.server_port)
                self.ready.set()

                while True:
                    for key, mask in sel.select():
                        if key.fileobj is server:
                            conn, addr = server.accept()
                            conn.setblocking(False)
                            sel.register(conn, selectors.EVENT_READ,
                                         data=types.SimpleNamespace(addr=addr, inb=b"", outb=b""))
                            logger.info("%s accepted connection from %s", self.name.decode(), addr)
                            continue

                        conn, data = key.fileobj, key.data
                        if mask & selectors.EVENT_READ:
                            chunk = conn.recv(1024)
                            if not chunk:
                                sel.unregister(conn)
                                conn.close()
                                logger.info("%s closed connection from %s", self.name.decode(), data.addr)
                                continue
                            data.inb += chunk
                            # A newline terminates one complete TCP application message.
                            if b"\n" not in data.inb:
                                continue
                            message, _, data.inb = data.inb.partition(b"\n")
                            try:
                                self.route_passenger(message)
                                data.outb = b"OK\n"
                            except Exception:
                                logger.exception("%s could not route %r", self.name.decode(), message)
                                data.outb = b"ERROR\n"
                            sel.modify(conn, selectors.EVENT_WRITE, data=data)

                        if mask & selectors.EVENT_WRITE and data.outb:
                            sent = conn.send(data.outb)
                            data.outb = data.outb[sent:]
                            if not data.outb:
                                sel.unregister(conn)
                                conn.close()
        except Exception:
            logger.exception("Server failed for %s", self.name.decode())
            self.ready.set()
        finally:
            sel.close()

    def route_passenger(self, message):
        origin, final_dest, passenger = message.split(b", ", 2)
        if origin not in LOOKUP or final_dest not in LOOKUP:
            raise ValueError("Unknown airport in passenger message")
        airport = self.name.decode()
        logger.info("%s received passenger %s (origin %s, destination %s)",
                    airport, passenger.decode(), origin.decode(), final_dest.decode())

        if self.name == origin:
            logger.info("Passenger %s departing %s for %s",
                        passenger.decode(), origin.decode(), final_dest.decode())
        if self.name == final_dest:
            logger.info("Passenger %s arrived at final destination %s",
                        passenger.decode(), final_dest.decode())
            return

        next_hop = final_dest
        if DIRECT[airport_index[self.name]-1][airport_index[final_dest]-1] == 0:
            if self.name in HUBS:
                raise ValueError("Hub has no direct route to destination")
            next_hop = (b"ANC" if DIRECT[airport_index[self.name]-1][1]
                        else b"SEA")
            logger.info("Passenger %s requires layover at %s", passenger.decode(), next_hop.decode())

        logger.info("Passenger %s forwarded %s (%s) -> %s (%s)",
                    passenger.decode(), airport, LOOKUP[self.name],
                    next_hop.decode(), LOOKUP[next_hop])
        # Wait for the downstream airport's acknowledgement before replying upstream.
        # This keeps a passenger's log entries in travel order.
        self.start_client(next_hop, self.server_port, message)

    def start_client(self, dest_host, dest_port, data):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((LOOKUP[self.name], 0))
            sock.connect((LOOKUP[dest_host], dest_port))
            sock.sendall(data + b"\n")
            response = sock.recv(1024)
            if response != b"OK\n":
                raise RuntimeError(f"Unexpected response from {dest_host!r}: {response!r}")
            logger.info("%s received completion acknowledgement from %s",
                        self.name.decode(), dest_host.decode())

@dataclass
class manager:

    payload : str = ""
    origin = b""
    #ip = "127.0.0.18"

    def run(self):
        self.collect_payload()
        self.start_client()
        

    def collect_payload(self):
        def ask_airport(prompt):
            while True:
                airport = input(prompt).strip().upper()
                if airport.encode("ascii", errors="ignore") in LOOKUP and airport.isascii():
                    return airport
                print(f"Invalid airport code: {airport or '(blank)'}. Please enter a listed IATA airport code.")

        origin = ask_airport("Please enter your origin: ")
        destination = ask_airport("Please enter your destination: ")
        passenger = input("Please enter your name: ").strip()
        self.origin = origin.encode("ascii")
        self.payload = f"{origin}, {destination}, {passenger}"

    def start_client(self):
        logger.info("Manager submitting passenger: %s", self.payload)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.18", 0))
            sock.connect((LOOKUP[self.origin], LISTENING_PORT))
            sock.sendall(self.payload.encode("utf-8") + b"\n")
            response = sock.recv(1024)
            if response != b"OK\n":
                raise RuntimeError(f"Passenger routing failed: {response!r}; see air_traffic.log")
        logger.info("Manager confirmed delivery: %s", self.payload)
        print("Passenger arrived at destination. (Details saved to air_traffic.log)")
        self.payload = ""
        self.origin = b""


if __name__ == "__main__":
    for name, ip in LOOKUP.items():
        temp = node(name, ip, LISTENING_PORT, name in HUBS)
        t = threading.Thread(target=temp.start_server, name=f"Airport-{name.decode()}", daemon=True)
        airports.append(temp)
        airport_threads.append(t)
        airport_index[name] = node.index

    for t in airport_threads:
        t.start()

    # Do not request input until all airport servers have finished initialization.
    for airport, t in zip(airports, airport_threads):
        airport.ready.wait()
        if not t.is_alive():
            raise RuntimeError(f"Could not start {airport.name.decode()}; see air_traffic.log")

    print(f"{len(airports)} airports ready. Activity is logged to air_traffic.log")
    airport_manager = manager()
    try:
        while True:
            try:
                airport_manager.run()
            except ValueError as exc:
                print(f"Invalid input: {exc}")
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
