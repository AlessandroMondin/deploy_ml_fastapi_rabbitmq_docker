import ast
import logging
import requests
import time

logger = logging.getLogger(__name__)


class PikaBatchHandler:
    def __init__(self, channel, callback_fn, max_batch_size: int, batch_timeout: int):
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout

        self.time_first_item = time.time()
        self.channel = channel
        self.callback_fn = callback_fn
        self.batch = []
        self.queue_tags = []

    def on_request(self, ch, method, props, body):
        print("start at {}".format(time.time()))
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
            print("end at {}".format(time.time()))
            r = requests.post(self.batch[idx]["callback_url"], json=data)
            print(r)

        # Acknowledge all messages in the batch
        for method in self.queue_tags:
            self.channel.basic_ack(delivery_tag=method.delivery_tag)

        # Clear batch data
        self.batch = []
        self.queue_tags = []
