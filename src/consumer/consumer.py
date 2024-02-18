import base64
import cv2
import numpy as np
import os
import pika

from classifier import ImageClassifier

rabbitmq_user = os.getenv("RABBITMQ_DEFAULT_USER")
rabbitmq_pass = os.getenv("RABBITMQ_DEFAULT_PASS")
rabbitmq_host = os.getenv("HOSTNAMERABBIT")

credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
parameters = pika.ConnectionParameters(
    host=rabbitmq_host, port=5672, virtual_host="/", credentials=credentials
)

connection = pika.BlockingConnection(parameters)


channel = connection.channel()

channel.queue_declare(queue="rpc_queue", durable=True)

model = ImageClassifier("mobilenet_v3_large.onnx")


def on_request(ch, method, props, body):
    bin_img = base64.b64decode(body)
    nparr = np.frombuffer(bin_img, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    out = model(img)

    ch.basic_publish(
        exchange="",
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=str(out),
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue="rpc_queue", on_message_callback=on_request)
channel.start_consuming()
