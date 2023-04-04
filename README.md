# DVIC Demo Monitoring


## General Structure 

The DVIC Demo monitoring is a minimalist remote demo controller based on:

- A central server for log keeping and command deployment
- A daemon to run on each demo node, composed of a single, minimal, low dependency python3 script installed with systemd **on desktop nodes only**
- A library for common languages used at DVIC

The communication process between library and daemon uses a simple file in /tmp to store output logs.
Files should be named `dvic_log_<token>` where `<token>` is a randomly generated token.

## Architecture Diagram

```
┌───────┐
│Demo   │Write to temp file, 
│Process├─────────┐
└───────┘         │                                    ┌────────────────────┐
                  ▼                                    │                    │
┌───────┐    ┌──────────┐    POST requests for         │   Central Server   │
│Demo   ├───►│ Demo Node│    KeepAlive                 │                    │
│Process│    │ Script   ├─────────────────────────────►│   dvic.devinci.fr  │
└───────┘    └──────────┘    WebSockets for bi-direct  └────────────────────┘
                  ▲          communication and                 ▲
┌───────┐         │          sending commands            ┌──────────────┐
│Demo   ├─────────┘                                      │              │
│Process│                                                │  Dashboard   │
└───────┘                                                │              │
                                                         └──────────────┘
```


The Demo Processes are the user-made processes using the aforementioned library to write to log files.

The Demo script node is the self-sufficient script file.

The central server keeps a state map of the connected nodes and sends commands when requested


## APIs

### Central Server

The central server API receives keep alive signals, **especially from demos hosted on ESP32 nodes**

The API received and maintains bi-directional websocket streams.

The API exposes states for dashboard display.

## Protocol

Information is sent in JSON format.

Information types:
- Machine hardware State (temp, cpu, id, memory, disk, number of procs etc)
- Machine log (system logs)
- Machine demo proc state (Is Alive ?)
- Machine demo logs (each time a log is written, send it to central server)
- Shell command response (when a command is sent to a node, send back the result)

### Installation procedure

New node joining the network:

- Node addition request from client (CLI/Dashboard). Gives IP, username, password, source node
- Server generates a UUID for the new node
- Server generate a new private key for the node, saves the public key
- Server generates the installation script from the base script and updates the UUID and private key (or pushes them in separate files e.g config)
- Server starts interactive session in source node, ssh to the target IP with username and password
- Server executes the installation script through the SSHScriptInteractiveSession
- The new node should now be part of the network


## Roadmap

### Network

- [x] Websocket from node to central server
- [x] Bring back online the connection.
- [x] Define communication protocol

### Node

- [x] Execute command received from central server
- [x] Send data to central server
- [x] Gather data from hardware and soft sources (syslog, t° etc)
- [ ] Read log files from /tmp
- [ ] Inspect docker containers and read /tmp from there

- [ ] Self-update from central server request
- [ ] Automatic installation

### Central Server & Dashboard

- [x] Receive data from nodes
- [ ] Keep state history of metrics
- [x] Choose database for log
- [x] Choose log format
- [x] Keep log history in database 
- [x] Expose API for dashboard (node state, last logs etc)
- [ ] Terminal session from dashboard

### Libraries

- [ ] Library writes to /tmp
- [x] Implement log format with log level
- [ ] Write PID or other info on the first line (pid, exec, user etc)
- [ ] Deploy artifacts

### Quality Check

- Unit test and TDD all the way
- CI/CD pipeline with MVP