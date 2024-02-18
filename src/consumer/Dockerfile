# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /usr/src/app

# 3rd party lib to use open-cv 
RUN apt update; apt install -y libgl1

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable
ENV MODEL_PATH=/usr/src/app/mobilenet_v3_large.onnx

# Run main.py when the container launches
CMD ["python", "consumer.py"]
