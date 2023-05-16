# DVIC Demo Monitoring Node

Monitoring node connecting back to Central Server

This folder contains the node.py and different test pipelines.

The node functions are described in the [general readme](../README.md)

# To DO

- [ ] Auto-update python script
- [x] Send back the result of a command
- [x] Is the node alive ?

# Tests

In order to launch the tests, you need to run the api in local mode.
Then, you can run the tests with the following command:

```bash
source tests/exports.sh
make test
```

# Updater

Updating the software is done from the central server:

- Launch update script
- Script downloads the update from a given source
- Script overrides current version
- SCript restarts the software