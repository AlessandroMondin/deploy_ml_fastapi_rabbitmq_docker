import ast
from typing import List


import cv2
import numpy as np

import torch
from torchvision.models import vit_b_16
from torchvision.models import ViT_B_16_Weights


class ImageClassifier:
    with open("imagenet1000_clsidx_to_labels.txt") as f:
        data = f.read()
    js = ast.literal_eval(data)

    def __init__(self) -> None:
        self.model = vit_b_16(weights=ViT_B_16_Weights.DEFAULT)
        self.preprocessing = ViT_B_16_Weights.DEFAULT.transforms()

    def __call__(self, img: np.ndarray) -> List:

        if len(img.shape) == 3:
            batch = torch.from_numpy(img)
            batch = torch.permute(batch, (2, 0, 1))[None, ...]
        elif len(img.shape) == 4:
            batch = torch.from_numpy(img)
            batch = torch.permute(batch, (0, 3, 1, 2))[None, ...]

        batch = self.preprocessing(batch)

        outputs = self.model(batch)
        # Run the model
        logs = torch.softmax(outputs.flatten(), 0)
        _, top_5_indices = torch.topk(logs, 5)
        top_5_labels = [self.js[id.item()].split(",")[0] for id in top_5_indices]

        return top_5_labels

    def softmax(self, x):
        """Compute softmax values for each sets of scores in x."""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()


if __name__ == "__main__":
    # Load and preprocess the labels for ImageNet
    with open("imagenet1000_clsidx_to_labels.txt") as f:
        data = f.read()
    js = ast.literal_eval(data)

    model = ImageClassifier()
    img = cv2.imread("/Users/alessandro/rabbit-mq-exp/data/tiger_shark.jpg")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    output = model(img)

    print(output)
