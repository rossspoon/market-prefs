import asyncio
import itertools
import json
import websockets
from threading import Thread
import os

from rounds import Player

SOCKETS = []

def register_bio_user(code):
    #for p in Player.filter():
    print(f"Got it: {code}")

async def handler(websocket):
    SOCKETS.append(websocket)
    print(websocket)
    while True:
        message = await websocket.recv()
        msg = json.loads(message)
        print(msg)
        type = msg.get("type")

        if type == 'register':
            part_code = msg.get("code")
            register_bio_user(part_code)



async def main():
    async with websockets.serve(handler, "", port=int(os.enviror["PORT"])):
        await asyncio.Future() # run Forever


def signal_thread():
    print("starting websocket receiver")
    asyncio.run(main())
    print("finishing signal_thread")


_t = Thread(target=signal_thread)
_t.setDaemon(True)
_t.start()
print(f"started thread in {__name__}")
