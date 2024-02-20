import json
import os

import pika

from logger import get_logger

logger = get_logger(__name__)

rabbitmq_user = os.getenv("RABBITMQ_DEFAULT_USER")
rabbitmq_pass = os.getenv("RABBITMQ_DEFAULT_PASS")
rabbitmq_host = os.getenv("HOSTNAMERABBIT")

credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
parameters = pika.ConnectionParameters(
    host=rabbitmq_host,
    port=5672,
    virtual_host="/",
    credentials=credentials,
    heartbeat=600,
)


class RabbitProducer(object):

    def __init__(self):

        self.parameters = parameters
        self._connection = None
        self._channel = None
        self.connect()

    # reconnection strategy: https://stackoverflow.com/a/35730562
    def push(self, n):
        try:
            self._push(n)
        except pika.exceptions.ChannelWrongStateError:
            logger.warning("Connection was lost, reconnecting..")
            self.connect()
            self._push(n)

    def _push(self, n):
        self._channel.basic_publish(
            exchange="",
            routing_key="rpc_queue",
            body=json.dumps(n),
        )

    def connect(self):
        if not self._connection or self._connection.is_closed:
            self._connection = pika.BlockingConnection(self.parameters)
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue="rpc_queue", durable=True)

            logger.info("Connection estabilished.")
