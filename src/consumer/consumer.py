import base64
import os
from typing import List

import cv2
import numpy as np
import pika

from classifier import ImageClassifier
from batch_handler import PikaBatchHandler

from logger import get_logger

logger = get_logger(__name__)

# LOAD ENVIRONMENT VARIABLES
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE"))
BATCH_TIMEOUT = float(os.getenv("BATCH_TIMEOUT"))
rabbitmq_user = os.getenv("RABBITMQ_DEFAULT_USER")
rabbitmq_pass = os.getenv("RABBITMQ_DEFAULT_PASS")
rabbitmq_host = os.getenv("HOSTNAMERABBIT")

# LOAD RABBITMQ (pika) PARAMETERS
credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
parameters = pika.ConnectionParameters(
    host=rabbitmq_host,
    port=5672,
    virtual_host="/",
    credentials=credentials,
    heartbeat=600,
    # socket timeout might give headaches to troubleshoot
    socket_timeout=2,
)

# LOAD MODEL
model = ImageClassifier("mobilenet_v3_large.onnx")


# CALLBACK FUNCTION EXECUTES BY THE PikaBatchHandler
def callback(batch: List) -> List:
    if not batch:
        return
    imgs = [body["file"] for body in batch]
    imgs = [base64.b64decode(img) for img in imgs]
    imgs = [np.frombuffer(bin_img, np.uint8) for bin_img in imgs]
    imgs = [cv2.imdecode(nparr, cv2.IMREAD_COLOR) for nparr in imgs]
    outs = model(imgs)
    return outs


handler = PikaBatchHandler(
    pika_connection_parameters=parameters,
    callback_fn=callback,
    max_batch_size=MAX_BATCH_SIZE,
    batch_timeout=BATCH_TIMEOUT,
)
handler.setup_and_consume()
