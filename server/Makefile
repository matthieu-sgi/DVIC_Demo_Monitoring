run:
	uvicorn dvic_log_server.api:app --ws-ping-interval 2 --ws-ping-timeout 1

run_local:
	DISABLE_CRYPTO=1 uvicorn dvic_log_server.api:app --ws-ping-interval 2 --ws-ping-timeout 1 --log-level=debug