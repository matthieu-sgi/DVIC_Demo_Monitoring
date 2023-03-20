# DVIC Demo Monitoring Central Server

The Central server receives connections from the nodes and maintains state of the demo. It also keeps the logs and stats for the dashboard.

The roadmap for the central server is in the [general readme](../README.md)

## Databases

> **Note**
>
> Most likely going with ELK for log keeping and Influx for state

## Tests

In order to run the api local and the elk stack, run :

```bash
make run_local
```
If you want to stop the elk stack, run :

```bash
make stop_database
```