# Machine Learning Pipeline using FastAPI, RabbitMQ and image classifier (ONNX)

This inference pipeline is composed by a producer, a RabbitMQ queue and a consumer. FYI, in the text below each variable written in `CAPITAL-YELLOW` is defined in the `docker-compose.yaml`.

- The producer receives post requests (_base64_ encoded images) and pushes messages to the RabbitMQ queue where each message is composed by a unique id (UUID), an image, a `CALLBACK_URL` (webhook for asynchronous response) and the _time.time()_ where the image was sent. If no response is received after `TIMEOUT` seconds, the client will receive an _error 400_. Check files at **src/producer**.
- The consumer receives simoultaneously up to `MAX_BATCH_SIZE` and processes them in batches. However, once the first message is received, all messages will be processed after `BATCH_TIMEOUT` seconds, even if they are fewer then `MAX_BATCH_SIZE`. Once a message is processed, it is removed from the RABBITMQ queue (_channel.basic_ack_) and is sent back to the producer.
- Response to client: once the processed message is sent back to the producer, if the response if received within a `TIMEOUT` time, then it is stored in a local dictionary. The initial asynchronous function used to receive client requests, checks every 0.01 seconds (sleeps asynchronously) if the server response is present within the local dictionary. If is present, it sends the response back to the client.

This pipeline could be further improved by using a "not TCP protocol" in the consumer-producer response.
<br>

# How to run:

### Build Images and run containers.

            docker compose up -d

FYI: RABBITMQ takes a while to setup, even if the container are present, wait some seconds before staring to send requests.

### Test the service:

            bash send_requests.sh

<br>

## How to configure rabbitMQ:

1.  Create a password hash with:

            python src/rabbitmq/password.py your_password

2.  Open `src/rabbitmq/definitions.json`, add create a dict within _users_:

        {
        "name": "your_user_name",
        "password_hash": "password_hash_created_at_point_1",
        "hashing_algorithm": "rabbit_password_hashing_sha256",
        "tags": ""
        }

3.  Still in `src/rabbitmq/definitions.json` make sure the user has the the specified permission under the _permissions_ key:

        {
        "user": "your_user_name",
        "vhost": "\/",
        "configure": ".*",
        "write": ".*",
        "read": ".*"
        }
