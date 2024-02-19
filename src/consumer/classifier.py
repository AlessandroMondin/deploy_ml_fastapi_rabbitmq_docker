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

    def __call__(self, imgs: List[np.ndarray]) -> List:
        imgs = [self.preprocess_image(img) for img in imgs]
        imgs = np.concatenate(imgs, axis=0)
        outputs = self.session.run(None, {"input": imgs})[0]
        # Apply softmax to outputs; ensure it's applied to each output vector separately
        probs = self.softmax(outputs)

        # Determine top 5 labels for each image in the batch
        top_5_labels_batch = []
        for log in probs:
            top5 = np.argpartition(log, -5)[-5:]
            top_5_labels = [self.js[id].split(",")[0] for id in top5]
            top_5_labels_batch.append(top_5_labels)

        return top_5_labels_batch

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
        """Compute softmax values for each set of scores in x along the last axis."""
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / e_x.sum(axis=-1, keepdims=True)
