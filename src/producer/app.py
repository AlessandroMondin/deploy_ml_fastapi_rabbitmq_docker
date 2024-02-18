from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse

from rpc import RPCHandler

app = FastAPI()
rpc_handler = RPCHandler()


@app.post("/predict/")
async def classify_img(file: UploadFile):

    file = await file.read()
    file = file.decode("utf-8")
    predictions = rpc_handler.call(file)
    # channel.basic_consume(queue="model.output")
    # TODO implement model.out queue consumer
    return JSONResponse(content={"predictions": predictions})
