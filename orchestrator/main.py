import time
from RMQueue import RMQueue


if __name__ == "__main__":
    queue = RMQueue()

    while True:
        message = queue.receive()
        if message:
            print(f"Received message: {message}", flush=True)
        else:
            print("No message received" , flush=True)
        #wait for 2 seconds
        #flush the output buffer


        time.sleep(2)
        
    queue.close()
#
    