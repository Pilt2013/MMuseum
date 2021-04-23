
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
import asyncio
import logging

playing = False
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

global video 

def play_tour(address, *args):
    print ("playTour")
    global playing
    playing = True

def play_waiting_handler(address, *args):
    print ("playWaiting")

def play_idle(address, *args):
    print ("playIdle")

def play_handler(address, *args):
    print ("playVideo")
    log.info (f"{address}: {args}")
    global playing
    playing = True

def handler_function(address, *args):
    log.info (f"{address}: {args}")
    global playing
    playing = True

dispatcher = Dispatcher()
dispatcher.map("/playVideo", play_handler)
dispatcher.map("/playWaiting", play_waiting_handler)
dispatcher.map("/playTour", play_tour)
dispatcher.map("/playIdle", play_idle)
dispatcher.set_default_handler(handler_function)
client = SimpleUDPClient("127.0.0.1", 7001)

ip = "127.0.0.1"
port = 7000


async def loop():

    global playing
    """Example main loop that only runs for 10 iterations before finishing"""
    while True:
        await asyncio.sleep(5)
        if playing == True:
            await asyncio.sleep(5)
            playing = False
            print ("play finished")
            client.send_message("/playFinished",1)

        client.send_message("/composition/layers/17/clips/2/connect",3)
        



async def init_main():
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    await loop()  # Enter main loop of program

    transport.close()  # Clean up serve endpoint


asyncio.run(init_main())