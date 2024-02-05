# class to control communication between the dashboard and the orchestrator

import json
import requests
import os
import pika

class Queue:
    def __init__(self):
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
        self.rabbitmq_port = os.getenv("RABBITMQ_PORT", 5672)
        self.rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
        self.rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")
        self.rabbitmq_queue = os.getenv("RABBITMQ_QUEUE", "pycontinuum")

    def send(self, message):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host, port=self.rabbitmq_port, credentials=pika.PlainCredentials(self.rabbitmq_user, self.rabbitmq_password)))
        channel = connection.channel()
        channel.queue_declare(queue=self.rabbitmq_queue)
        channel.basic_publish(exchange='', routing_key=self.rabbitmq_queue, body=message)
        connection.close()

    def receive(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host, port=self.rabbitmq_port, credentials=pika.PlainCredentials(self.rabbitmq_user, self.rabbitmq_password)))
        channel = connection.channel()
        channel.queue_declare(queue=self.rabbitmq_queue)
        method_frame, header_frame, body = channel.basic_get(queue=self.rabbitmq_queue)
        if method_frame:
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        connection.close()
        return body

    def get(self):
        response = requests.get(f"http://{self.rabbitmq_host}:{self.rabbitmq_port}/api/queues/%2F/{self.rabbitmq_queue}")
        return json.loads(response.text)

    def purge(self):
        response = requests.delete(f"http://{self.rabbitmq_host}:{self.rabbitmq_port}/api/queues/%2F/{self.rabbitmq_queue}/contents")
        return response.status_code

    def delete(self):
        response = requests.delete(f"http://{self.rabbitmq_host}:{self.rabbitmq_port}/api/queues/%2F/{self.rabbitmq_queue}")
        return response.status_code