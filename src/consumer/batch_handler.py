import ast
import logging
import requests
import time
from typing import Callable

import pika


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PikaBatchHandler:
    def __init__(
        self,
        pika_connection_parameters: pika.ConnectionParameters,
        callback_fn: Callable,
        max_batch_size: int,
        batch_timeout: int,
    ):
        self.pika_connection_parameters = pika_connection_parameters
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout

        self.time_first_item = time.time()
        self.callback_fn = callback_fn
        self.batch = []
        self.queue_tags = []

    def on_request(self, ch, method, props, body):
        # print("start at {}".format(time.time()))
        self.batch.append(body)
        self.queue_tags.append(method)
        # If the batch is completed we process it
        if (
            len(self.batch) == self.max_batch_size
            or (time.time() - self.time_first_item) > self.batch_timeout
        ):
            self.process()
        # Otherwise after the first element is added to the batch,
        # we process it after BATCH_TIMEOUT seconds
        elif len(self.batch) == 1:
            self.time_first_item = time.time()

    def process(self):
        self.batch = [ast.literal_eval(body.decode("utf-8")) for body in self.batch]
        images = [body["file"] for body in self.batch]
        outs = self.callback_fn(images)

        # Publish results
        for idx, result in enumerate(outs):
            self.batch[idx].pop("file")
            self.batch[idx]["predictions"] = result
            data = self.batch[idx]
            # print("end at {}".format(time.time()))
            r = requests.post(self.batch[idx]["callback_url"], json=data)
            if r.status_code != 200:
                logger.warning("Webhook to producer failed")

        # Acknowledge all messages in the batch
        for method in self.queue_tags:
            self.channel.basic_ack(delivery_tag=method.delivery_tag)

        # Clear batch data
        self.batch = []
        self.queue_tags = []

    def setup_and_consume(self):
        while True:
            try:
                connection = pika.BlockingConnection(self.pika_connection_parameters)
                self.channel = connection.channel()
                self.channel.queue_declare(queue="rpc_queue", durable=True)

                self.channel.basic_qos(prefetch_count=self.max_batch_size)
                self.channel.basic_consume(
                    queue="rpc_queue", on_message_callback=self.on_request
                )

                logger.info("Start consuming")
                self.channel.start_consuming()
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                continue  # Retry connection
