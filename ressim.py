
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
import asyncio
import logging

playing = []
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

global video 

def handler_function(address, *args):
    log.info (f"{address}: {args}")
    global playing
    playing.append(address)

dispatcher = Dispatcher()
dispatcher.set_default_handler(handler_function)
client = SimpleUDPClient("127.0.0.1", 7001)

ip = "127.0.0.1"
port = 7000


async def loop():

    global playing
    """Example main loop that only runs for 10 iterations before finishing"""
    while True:
        await asyncio.sleep(5)
        if playing:
            await asyncio.sleep(5)

            if playing[0].split("/")[3] == "16":

                print (f"play finished: {playing[0]}")
                client.send_message(playing[0] + "ed",1)
            playing.pop(0)


        #client.send_message("/composition/layers/17/clips/2/connect",3)
        



async def init_main():
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    await loop()  # Enter main loop of program

    transport.close()  # Clean up serve endpoint


asyncio.run(init_main())