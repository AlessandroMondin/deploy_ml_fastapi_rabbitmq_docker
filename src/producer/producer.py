import json
import os

import pika

rabbitmq_user = os.getenv("RABBITMQ_DEFAULT_USER")
rabbitmq_pass = os.getenv("RABBITMQ_DEFAULT_PASS")
rabbitmq_host = os.getenv("HOSTNAMERABBIT")

credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
parameters = pika.ConnectionParameters(
    host=rabbitmq_host, port=5672, virtual_host="/", credentials=credentials
)


class RabbitProducer(object):

    def __init__(self):

        self.connection = pika.BlockingConnection(parameters)

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue="rpc_queue", durable=True)
        self.callback_queue = result.method.queue

    def push(self, n):
        self.channel.basic_publish(
            exchange="",
            routing_key="rpc_queue",
            body=json.dumps(n),
        )
