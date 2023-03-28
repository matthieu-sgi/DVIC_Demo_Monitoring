run:
	uvicorn dvic_log_server.api:app --ws-ping-interval 2 --ws-ping-timeout 1

run_local:
	DISABLE_CRYPTO=1 python3 -m uvicorn dvic_log_server.api:app --ws-ping-interval 2 --ws-ping-timeout 1 --log-level=debug

launch_database:
	docker compose -f ./database/elk_stack/docker-compose.yaml up -d

stop_database:
	docker stop elk_stack-elk-1
