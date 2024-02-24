import asyncio
import os
import time
import uuid

from fastapi import FastAPI, UploadFile, HTTPException, Header, Depends
from fastapi.responses import JSONResponse

from producer import RabbitProducer

ENV = os.environ.get("ENV")
TIMEOUT = int(os.environ.get("TIMEOUT"))
CALLBACK_URL = os.environ.get("CALLBACK_URL")
API_KEY = os.environ.get("API_KEY")

app = FastAPI()

# Only add documentation endpoints if not in production
if os.environ.get("ENV") != "production":
    app = FastAPI(docs_url="/docs", redoc_url="/redoc")
else:
    app = FastAPI(docs_url=None, redoc_url=None)

producer = RabbitProducer()
predictions = {}


async def get_api_key(request_api_key: str = Header(...)):
    if request_api_key != API_KEY:
        raise HTTPException(status_code=400, detail="Invalid API Key")
    return request_api_key


@app.post("/receive")
async def store_predictions(file: dict, api_key: str = Depends(get_api_key)):
    # print("time received: {}".format(time.time()))
    if time.time() - file["sent_at"] <= TIMEOUT:
        predictions[file["id"]] = file["predictions"]


# Expects images to be already BASE64 encoded
@app.post("/predict/")
async def classify_img(file: UploadFile):
    file = await file.read()
    unique_id = str(uuid.uuid4())
    file = file.decode("utf-8")
    sent_at = time.time()
    body = {
        "id": unique_id,
        "callback_url": CALLBACK_URL,
        "file": file,
        "sent_at": sent_at,
    }
    producer.push(body)
    while time.time() - sent_at < TIMEOUT:
        if unique_id in predictions:
            result = predictions.pop(unique_id)
            if result is not None:
                break

        await asyncio.sleep(0.01)
    else:
        raise HTTPException(
            status_code=400, detail="Prediction failed after {} seconds".format(TIMEOUT)
        )

    return JSONResponse(content={"classes": result})
