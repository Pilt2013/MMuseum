import asyncio
import logging
import time
import numpy as np

# Classes
from ResolumeQueue import ResQueue
from async_modbus import modbus_for_url
# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)




class SwitchBox:
    def __init__(self, url, loop, num_switches = 4):

        self.url = url
        self.client = modbus_for_url(self.url)
        self.switchstate = np.zeros((4),dtype=np.uint8)
        self.old_switchstate = np.zeros((4),dtype=np.uint8)
        self.num_switches = num_switches
        self.loop = loop

    def timeout(self):
        log.warning (f"Timeout talking to box {self.url}")

    async def read_inputs(self):
        while True:
            self.old_switchstate = self.switchstate
            try:
                TimeoutCallback = self.loop.call_later(5, self.timeout)
                self.switchstate = await self.client.read_discrete_inputs(slave_id=0, starting_address=0, quantity=self.num_switches)   
                TimeoutCallback.cancel()
            except Exception as e:
                log.warning(e)

            if not np.array_equal(self.old_switchstate,self.switchstate):
                log.debug("Switch changed %s %s", self.url,self.switchstate)

            await asyncio.sleep(0.1) #Maybe not needed

async def main_loop(switchboxes):

    log.debug ("Starting Main Loop")

    resolume_queue = ResQueue()
    await resolume_queue.startOSCserver()

    resolume_queue.play_idle_video()
    #resolume_queue.play_tour_video()

    while True:
        #log.debug("Main handler loop")

        #Combine all the switchstates into one array
        a = switchboxes[0].switchstate
        for i in range(1,len(switchboxes)):
            a = np.concatenate((a, switchboxes[i].switchstate), axis=None)

        #Handle button press -> Add to queue
        if (any(a)):
            for i in range(len(a)):
                if a[i] == 1:
                    resolume_queue.enqueue(i)

        #Add some code to play idle video when tour finished           

        #if resolume_queue.isEmpty() and (resolume_queue.playing_tour_video == False):
        #    resolume_queue.play_idle_video(5)

        await asyncio.sleep(0.1)

if __name__ == "__main__":
    #A3 RFID

    #9 switchboxes
    #4 swithes on each box
    #36 switches total 
    switchboxIPs = [
    "tcp://192.168.1.105:502",
    "tcp://192.168.1.106:502", 
    "tcp://192.168.1.107:502",
    "tcp://192.168.1.108:502",
    "tcp://192.168.1.109:502",
    "tcp://192.168.1.110:502",
    "tcp://192.168.1.111:502",
    "tcp://192.168.1.112:502",
    "tcp://192.168.1.113:502",
    ]

    #switchboxIPs = [
    #"tcp://192.168.1.105:502", 
    #]   

    loop = asyncio.get_event_loop()
    loop.set_debug(False)

    switchboxes = []
    #Create instances of clases
    for ip in switchboxIPs:
        switchboxes.append(SwitchBox(ip,loop))



    try:
        for box in switchboxes:
            loop.create_task(box.read_inputs())
            #asyncio.ensure_future(box.read_inputs())
        loop.create_task(main_loop(switchboxes))
        #asyncio.ensure_future(main_loop(switchboxes))

        loop.run_forever()
    except KeyboardInterrupt:

        pass
    finally:

        time.sleep(1)   
        # Stop loop:
        loop.stop()
        print("Shutdown complete ...")   
        loop.close()
