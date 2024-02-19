import base64
import cv2
import numpy as np
import os
import pika

from classifier import ImageClassifier
from batch_handler import PikaBatchHandler

rabbitmq_user = os.getenv("RABBITMQ_DEFAULT_USER")
rabbitmq_pass = os.getenv("RABBITMQ_DEFAULT_PASS")
rabbitmq_host = os.getenv("HOSTNAMERABBIT")

MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE"))
BATCH_TIMEOUT = float(os.getenv("BATCH_TIMEOUT"))

batch = []
batch_props = []

credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
parameters = pika.ConnectionParameters(
    host=rabbitmq_host, port=5672, virtual_host="/", credentials=credentials
)
connection = pika.BlockingConnection(parameters)

channel = connection.channel()
channel.queue_declare(queue="rpc_queue", durable=True)

model = ImageClassifier("mobilenet_v3_large.onnx")


def callback(batch: list):
    # Necessary for the timeout
    if not batch:
        return
    bin_imgs = [base64.b64decode(img) for img in batch]
    nparrs = [np.frombuffer(bin_img, np.uint8) for bin_img in bin_imgs]
    images = [cv2.imdecode(nparr, cv2.IMREAD_COLOR) for nparr in nparrs]
    outs = model(images)
    return outs


batch_handler = PikaBatchHandler(
    channel=channel,
    callback_fn=callback,
    max_batch_size=MAX_BATCH_SIZE,
    batch_timeout=BATCH_TIMEOUT,
)

channel.basic_qos(prefetch_count=MAX_BATCH_SIZE)
channel.basic_consume(queue="rpc_queue", on_message_callback=batch_handler.on_request)
channel.start_consuming()
