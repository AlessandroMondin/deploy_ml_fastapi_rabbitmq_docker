import ast
import uuid

from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse

# from fastapi.exceptions import HTTPException

import pika

app = FastAPI()


# rabbitmq_server = "localhost"
# queue_name = "exchange.input"

connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()

result = channel.queue_declare(queue="rpc_queue", durable=True)
callback_queue = result.method.queue


class RPCHandler(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="localhost")
        )

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue="", exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True,
        )

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange="",
            routing_key="rpc_queue",
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=n,
        )
        self.connection.process_data_events(time_limit=None)
        return ast.literal_eval(self.response.decode("utf-8"))


rpc_handler = RPCHandler()


@app.post("/predict/")
async def classify_img(file: UploadFile):

    file = await file.read()
    file = file.decode("utf-8")
    predictions = rpc_handler.call(file)
    # channel.basic_consume(queue="model.output")
    # TODO implement model.out queue consumer
    return JSONResponse(content={"predictions": predictions})
