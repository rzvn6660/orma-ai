import asyncio
import websockets

async def test():
    try:
        async with websockets.connect('ws://localhost:8000/api/wakeword/ws') as ws:
            print('Wakeword Connected!')
    except Exception as e:
        print(f"Wakeword Error: {e}")

    try:
        async with websockets.connect('ws://localhost:8000/api/notifications/ws/123') as ws:
            print('Notifications Connected!')
    except Exception as e:
        print(f"Notifications Error: {e}")

asyncio.run(test())
