import ast
import requests
import time
from typing import Callable

import pika

from logger import get_logger

logger = get_logger(__name__)


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
        self.batch.append(ast.literal_eval(body.decode("utf-8")))
        self.queue_tags.append(method)
        # If the batch is completed we process it
        if (
            len(self.batch) == self.max_batch_size
            or (time.time() - self.time_first_item) > self.batch_timeout
        ):
            self.process_messages()
        # Otherwise after the first element is added to the batch,
        # we process it after BATCH_TIMEOUT seconds
        elif len(self.batch) == 1:
            self.time_first_item = time.time()

    def process_messages(self):
        outs = self.callback_fn(self.batch)
        # Publish results
        for idx, result in enumerate(outs):
            # remove file key
            self.batch[idx].pop("file")
            # add predictions key
            self.batch[idx]["predictions"] = result
            data = self.batch[idx]
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
        failed_attempts = 0
        while True:
            try:
                connection = pika.BlockingConnection(self.pika_connection_parameters)
                self.channel = connection.channel()
                self.channel.queue_declare(queue="rpc_queue", durable=True)

                self.channel.basic_qos(prefetch_count=self.max_batch_size)
                self.channel.basic_consume(
                    queue="rpc_queue", on_message_callback=self.on_request
                )
                failed_attempts = 0
                logger.info("Start consuming")
                self.channel.start_consuming()

            except Exception as e:
                # Retry connection
                logger.error(f"Unexpected error: {e}", exc_info=True)
                failed_attempts += 1
                time.sleep(1)
                if failed_attempts > 50:
                    logger.error("Initialisation failed. Consumer not working.")
                    break
