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

> Please find an example log in the Example folder. The log in the root folder will be overwritten once the program has run.

**Example routes:**
- ANC → FAI (direct)
- FAI → ANC → BRW (layover)
- JNU → SEA → KTN (layover)

## 2. Network Simulation and Internet Exchange Points

This simulation is similar to how traffic moves through the Internet, where smaller networks may rely on larger networks or exchange points to reach their destinations. ANC and SEA serve as hubs that receive passengers and forward them to other airports when needed, similar to how routers forward data between networks.

The adjacency matrix defines which airports have direct connections, while the passengers represent traffic moving through the network. Each airport checks the destination of a passenger and determines whether the passenger has arrived or needs to be forwarded to another airport.

One difference from the actual Internet is that my simulation uses fixed connections and only allows one layover. It does not account for changes in network availability or more complex routing paths.

## 3. Assumptions and Reflection

**Assumptions:**
- Only ANC and SEA function as hubs.
- Passengers can have at most one layover.
- No direct flights exist between smaller airports.
- All airports run locally using loopback IP addresses.
- Airport connections remain fixed during execution.
- If a passenger has the same destination as origin, only a connection to the origin will be made. The log will explain that the passenger departed and then arrived at the same airport.
- It is possible for a hub to have a direct outgoing connection to a smaller airport even when that smaller airport does not have a direct return connection to the same hub.
- Some smaller airports connect with both hubs, while others only connect with one

This assignment helped me better understand how sockets can be used to communicate between different nodes. I also found it useful to separate the network topology from the routing logic, since the connections between airports determine how passengers can travel through the network.

I used threads to allow each airport to operate as a server while also being able to send messages to other airports using TCP sockets. One limitation of my implementation is that all airports run within the same process rather than independently. Additionally, the routing table is static, so the program cannot adjust if a connection between airports becomes unavailable.

## 4. Acknowledgements
I used a tutorial from [Real Python](https://realpython.com/python-sockets/) as reference for how to use sockets and how to run multiple airports at once. Specifically, the concept of selectors was heavily inspired by this tutorial.