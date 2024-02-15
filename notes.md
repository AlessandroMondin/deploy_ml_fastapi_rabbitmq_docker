### Download / run rabbitMQ

        docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management

### download rabbitmqadmin

link: https://www.rabbitmq.com/management-cli.html

### setup cli tool (UNIX, MacBook):

        sudo cp /Users/alessandro/Downloads/rabbitmqadmin /usr/local/bin/
        sudo chmod +x /usr/local/bin/rabbitmqadmin
        rabbitmqadmin --version

### list queues and list exchanges:

        rabbitmqadmin list queues
        rabbitmqadmin list exchanges
