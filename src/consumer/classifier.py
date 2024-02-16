import ast
from typing import List


import cv2
import numpy as np
import onnxruntime as ort


class ImageClassifier:
    with open("imagenet1000_clsidx_to_labels.txt") as f:
        data = f.read()
    js = ast.literal_eval(data)

    def __init__(self, path_to_onnx) -> None:
        self.session = ort.InferenceSession(path_to_onnx)

    def __call__(self, img: np.ndarray) -> List:
        img = self.preprocess_image(img)
        # Run the model
        outputs = self.session.run(None, {"input": img})
        logs = self.softmax(outputs[0]).flatten()
        top5 = np.argpartition(logs, -5)[-5:]
        top_5_labels = [self.js[id].split(",")[0] for id in top5]

        return top_5_labels

    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        # Load the image

        # https://stackoverflow.com/questions/71341354/cnn-why-do-we-first-resize-the-image-to-256-and-then-center-crop-to-224
        height, width, _ = img.shape
        scale = 256 / min(height, width)
        img = cv2.resize(img, (int(width * scale), int(height * scale)))

        # Center crop
        height, width, _ = img.shape
        startx = width // 2 - (224 // 2)
        starty = height // 2 - (224 // 2)
        img = img[starty : starty + 224, startx : startx + 224]

        # Convert to float32 and normalize
        img = img.astype(np.float32) / 255.0
        img -= np.array([0.485, 0.456, 0.406])
        img /= np.array([0.229, 0.224, 0.225])

        # HWC to CHW format
        img = img.transpose(2, 0, 1)

        # Add a batch dimension
        img = img[None, ...]
        return img

    def softmax(self, x):
        """Compute softmax values for each sets of scores in x."""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()


if __name__ == "__main__":
    # Load and preprocess the labels for ImageNet
    with open("imagenet1000_clsidx_to_labels.txt") as f:
        data = f.read()
    js = ast.literal_eval(data)

    model = ImageClassifier("mobilenet_v3_large.onnx")
    img = cv2.imread("/Users/alessandro/rabbit-mq-exp/data/tiger_shark.jpg")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    output = model(img)

    print(output)
