import base64
import cv2
import numpy as np
import pika

from classifier import ImageClassifier

connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))

channel = connection.channel()

channel.queue_declare(queue="rpc_queue", durable=True)

model = ImageClassifier()


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
