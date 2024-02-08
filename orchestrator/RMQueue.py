#class to manage communication between the dashboard and the queue

import json
import socket
import time
import requests
import pika
import os
from dotenv import load_dotenv

load_dotenv()

class RMQueue:
    def __init__(self):
        # try 10 times to connect to the broker
        for i in range(10):
            try:
                # declare broker connection
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
                self.channel = self.connection.channel()
                break
            except Exception as e:
                print(f"Error connecting to broker: {e}")
                print(f"Retrying in 5 seconds...")
                time.sleep(5)
        else:
            print("Failed to connect to broker")
            raise Exception("Failed to connect to broker")

        # declare queue
        self.channel.queue_declare(queue="DSB-ORC")

    def send(self, message):
        self.channel.basic_publish(exchange='', routing_key="DSB-ORC", body=message)

    def receive(self):
        method_frame, header_frame, body = self.channel.basic_get(queue="DSB-ORC")
        if method_frame:
            return body.decode("utf-8")
        else:
            return None

    def close(self):
        self.connection.close()

