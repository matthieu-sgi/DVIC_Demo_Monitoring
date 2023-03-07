# ELK stack

## Requirements

- Docker
- Docker Compose plugin (sudo apt install docker-compose-plugin)

YOu also have to set the virtual memory of your machine to at least 262144 (256MB). To do so, run the following command:

```bash
sudo sysctl -w vm.max_map_count=262144
```
If you want to make this change permanent, add the following line to your /etc/sysctl.conf file:

```bash
vm.max_map_count=262144
```

## Launching the stack

To launch the ELK stack, run the following command:

```bash
docker compose up [-d to detach]
``` 