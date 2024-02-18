import json
import pika

class LogQueue:
    def __init__(self, host='localhost', port=5672, queue_name='log'):
        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host, port=self.port, heartbeat=0)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            print(f"Connected to RabbitMQ on {self.host}:{self.port}, queue '{self.queue_name}'")
        except pika.exceptions.AMQPConnectionError as error:
            print(f"Failed to connect to RabbitMQ: {error}")
            # Handle connection error (e.g., retry connection)


    def send(self, message):
        if self.channel is not None:
            message_str = json.dumps(message)
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=message_str.encode('utf-8'),  # Ensure message is in bytes
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
        else:
            print("RabbitMQ channel is not established. Message not sent.")

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("RabbitMQ connection closed.")