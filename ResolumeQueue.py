import logging
import asyncio
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

#Deck 1 is main loop and tour video
#Column 1 always tour video
#Column 2 always idle video

#Deck 2 is cabinets

#Layer 17 is tour video - clip 2
#boxes will be on layer 16  starting at column 11 (/composition/layers/16/clips/11/connect)
#waiting videos on 13,14,15

class ResQueue:
    def __init__(self):
        
        #User configurable parameters
        self.limit = 4
        self.tour_video_layer = 17 
        self.tour_video_clip = 2
        self.tour_video_button_id = 0 

        self.box_video_layer = 16
        self.box_video_start_column = 11
        self.box_waiting_video_layer = 15

        #OSC related 
        self.osc_client = SimpleUDPClient("127.0.0.1", 7000)
        self.osc_dispatcher = Dispatcher()
        self.osc_dispatcher.map("/composition/layers/*/clips/*/connect", self.video_handler)
        self.osc_dispatcher.set_default_handler(self.debug_handler)

        #Internal variables
        self.items = []
        self.current_clip = 0
        self.current_layer = 0
        self.playing_tour_video = False
        self.playing_idle_video = False
        self.loop = asyncio.get_running_loop()
        self.current_box_waiting_video_layer = self.box_waiting_video_layer
        
    async def startOSCserver(self):
        self.osc_server = AsyncIOOSCUDPServer(("127.0.0.1", 7001), self.osc_dispatcher, self.loop)
        transport, protocol = await self.osc_server.create_serve_endpoint()  # Create datagram endpoint and start serving
    
    def clear(self):
        self.items = []  

    def inQueue(self,item):
        return (item in self.items)

    def isEmpty(self):
        return not self.items

    def enqueue(self, item):
        log.info (f"Added item to queue {item}")
        #Disable the queue if the tour video is playing
        if self.playing_tour_video == True:
            return

        if item == self.tour_video_button_id:
            self.play_tour_video()
            return

        if item not in self.items:
            if self.size() < self.limit:
                #Only play the waiting box video if something is in the queue
                if not self.isEmpty():
                    self.play_box_waiting_video(item) 
                else:
                    self.play_box_video(item)
                self.items.insert(0, item)  # list function
            else:
                log.info("Queue is full...")

    def play_tour_video(self):
        self.playing_idle_video = False
        self.clear() #Empty the queue (It could be made to resume queue)
        #Do we need to do anything about a potential waiting video that is playing or will mike handle that
        log.info ("Playing Tour video")
        self.playing_tour_video = True
        self._play_clip(self.tour_video_layer, self.tour_video_clip)
        

    def play_box_video(self, box):
        self.playing_idle_video = False
        log.info ("Playing box video %d", box)
        self._play_clip(self.box_video_layer, self.box_video_start_column + box)

    def play_box_waiting_video(self,box):
        self.playing_idle_video = False
        log.info ("Playing box waiting video %d", box)
        self._play_clip(self.current_box_waiting_video_layer, self.box_video_start_column + box)

        #Check below
        self.current_box_waiting_video_layer = self.current_box_waiting_video_layer - 1
        if self.current_box_waiting_video_layer == (self.box_waiting_video_layer - self.limit + 1):
           self.current_box_waiting_video_layer = self.box_waiting_video_layer

    def play_idle_video(self, delay=0):        
        if (self.playing_idle_video == False):
            log.info ("Playing Idle video in %d seconds",delay)
            self.loop.call_later(delay, self._play_idle_video)
            #Note: Assume no callback for this video and it loops forever in resolume?
            #Would a callback be better?
        self.playing_idle_video = True

    def _play_idle_video(self):
        log.info ("Playing idle video")
        self._play_column(3)

    def _change_deck(self, deck):
        self.osc_client.send_message(f"/composition/decks/{deck}/select", 1) 
  
    def _play_column(self, column):
        self.osc_client.send_message(f"/composition/columns/{column}/connect", 1)
        
        #self.osc_client.send_message("/composition/selectedcolumn/connect",1)
 
    def _play_clip(self, layers, clip):
        self.osc_client.send_message(f"/composition/layers/{layers}/clips/{clip}/connect", 1)
        self.current_layer = layers
        self.current_clip = clip

    def dequeue(self):
        try:
            self.items.pop()  # list function
        except IndexError:
            print(f"Queue empty...")

    def size(self):
        return len(self.items)
    def item_list(self):
        return list(self.items)
    def print_queue(self):
        log.info(f"Queue: {self.items}")
        # for items in self.items:
            # print(items)

    # not first in first out, this will remove the first value it finds from the value given
    def dequeue_remove(self, item):
        # print(f"Item number: {item}")
        # print(f"Current Queue: {self.items}")
        try:
            self.items.remove(item)
        except ValueError:
            log.warning("Button ID does not exist in queue...")


        #Calback from resolume to say a video has finished playing
    def debug_handler(self, address, *args):

        log.warning (f"Unhandled OSC from Resolume {address}: {args}")
        



        #Calback from resolume to say a video has finished playing
        #Format of "/composition/layers/*/clips/*/connect"
    def video_handler(self, address, *args):

        log.debug (f"OSC from Resolume {address}: {args}")

        data = address.split("/")
        try:
            layer = int(data[3])
            clip = int(data[5])
        except:
            log.error(f"Could not process address: {address}")
            return

        #Tour video handling
        if self.playing_tour_video == True:
            if (layer == self.tour_video_layer) and (clip == self.tour_video_clip) and (args[0] == 3):
                self.playing_tour_video = False
                log.info ("Finished playing Tour Video")
            return

        #Any return from the idle video??
        #Is this even needed (do we need to keep playing idle video or will it loop in resolume)
        #Instead of using a flag, we should proably check the callback id from rsolume
        #Might need a different dispatcher?
        if self.playing_idle_video == True:
            self.playing_idle_video = False
            log.info ("Finished playing Idle Video")
            return        
        
        if (layer == self.current_layer) and (clip == self.current_clip) and (args[0] == 3):
            #Remove item just played
            self.dequeue()

            #check queue
            if not self.isEmpty():
                #play next video
                self._play_clip(2, self.items[-1])
                log.info("playing Video %d", self.items[-1])
            else:
                log.info ("Finished playing queue")

