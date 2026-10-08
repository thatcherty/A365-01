# Assignment 1 – Socket Programming

## Overview

This program simulates Alaska Airlines traffic using a hub-and-spoke network. Each airport is represented by a node that can send and receive passengers using TCP sockets. Anchorage (ANC) and Seattle (SEA) are the only hubs.

The program uses 17 airports, with an adjacency matrix defining direct connections and a lookup dictionary mapping airport codes to IP addresses.

## 1. Running the Program

**Requirements:** Python 3 (standard library only).

Run the program using:

```bash
python node.py
```

All airport servers start automatically. Enter the origin airport, destination airport, and passenger name when prompted. Airport codes are validated against the supported airports.

The program determines whether a direct flight is available or a layover is required. Network activity is recorded in `air_traffic.log`.

**Example routes:**
- ANC → FAI (direct)
- FAI → ANC → BRW (layover)
- JNU → SEA → KTN (layover)

## 2. Network Simulation and Internet Exchange Points

The airport network resembles Internet routing, where smaller networks connect through larger networks or exchange points. ANC and SEA act as hubs that forward passengers to their destinations, similar to routers forwarding data.

The adjacency matrix represents the static network topology, while passengers represent dynamic network traffic. Each node reads the destination from the message and forwards it when necessary.

Unlike the actual Internet, this simulation uses a fixed topology and limits passengers to one layover.

## 3. Assumptions and Reflection

**Assumptions:**
- Only ANC and SEA function as hubs.
- Passengers can have at most one layover.
- No direct flights exist between smaller airports.
- All airports run locally using loopback IP addresses.
- Airport connections remain fixed during execution.

This assignment helped demonstrate how messages can move between independent nodes using sockets. Implementing the topology separately from the message-routing logic also helped show how a network's structure differs from the traffic traveling through it.

The program uses threads to manage airport servers and TCP connections for communication. One limitation is that the entire network runs within a single process rather than using separate processes or computers. The static routing table also does not account for changes in network availability.