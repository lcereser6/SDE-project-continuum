import json
import pika
import threading
import time
import psycopg2
from psycopg2 import sql

class LogQueue:
    def __init__(self, host='localhost', port=5672, queue_name='log', db_config=None):
        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.db_config = db_config
        self.messages = []
        self.lock = threading.Lock()
        self.batch_size = 15
        self.timeout = 3  # seconds
        self.last_message_time = None
        self.running = True

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

    def start_consuming(self):
        threading.Thread(target=self._consume_messages, daemon=True).start()

    def _consume_messages(self):
        while self.running:
            method_frame, header_frame, body = self.channel.basic_get(queue=self.queue_name)
            if method_frame:
                self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                message = json.loads(body.decode('utf-8'))
                with self.lock:
                    self.messages.append(message)
                    if not self.last_message_time:
                        self.last_message_time = time.time()
                self._check_batch_conditions()
            else:
                time.sleep(0.1)  # No message, wait a bit

    def _check_batch_conditions(self):
        with self.lock:
            if len(self.messages) >= self.batch_size or (time.time() - self.last_message_time >= self.timeout and self.messages):
                self._write_to_db()
                self.messages = []
                self.last_message_time = None

    def _write_to_db(self):
        # Implement the logic to write messages to the database
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            query = sql.SQL("INSERT INTO logs (action_uid,service, time, log_text) VALUES (%s, %s, %s, %s)")
            cur.executemany(query, [(msg['action_uid'],msg['service'], msg['time'], msg['log']) for msg in self.messages])
            conn.commit()
            cur.close()
            print(f"Wrote {len(self.messages)} messages to the database.")
        except Exception as e:
            print(f"Failed to write to the database: {e}")
        finally:
            if conn is not None:
                conn.close()

    def close(self):
        self.running = False
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("RabbitMQ connection closed.")
