'''Python script to test the load of the server'''

import pytest
import aiohttp
import asyncio

from server.dvic_log_server.network.packets import PacketHardwareState
from node.client.dvic_client import DVICClient

# async def send_packets(websocket):
#     while True:
#         try:
#             await asyncio.sleep(1/120)
#             pck = PacketHardwareState()  # Replace with actual packet data
#             await websocket.send_str(pck)
#         except aiohttp.ClientConnectionError:
#             break

# async def connect_and_send_packets(url, token):
#     session = aiohttp.ClientSession()
#     try:
#         async with session.ws_connect(f"{url}/ws/{token}") as websocket:
#             asyncio.create_task(send_packets(websocket))
#             async for msg in websocket:
#                 if msg.type == aiohttp.WSMsgType.TEXT:
#                     pass  # Do something with received messages
#                 elif msg.type == aiohttp.WSMsgType.ERROR:
#                     break
#     finally:
#         await session.close()

async def run_client(client : DVICClient):
    client.run()


@pytest.mark.asyncio
async def test_fastapi_websocket_load():
    url = "http://localhost:8000"
    token = "test_token"  # Replace with actual token
    num_clients = 1000  # Number of clients to simulate
    
    client : list[DVICClient] = []
    tasks = []
    for i in range(num_clients):
        client = DVICClient()
        
        tasks.append(asyncio.create_task(run_client(client)))
    
    for i in range(num_clients):
        tasks.append(asyncio.create_task(client.send_packet(PacketHardwareState())))

    await asyncio.gather(*tasks)
