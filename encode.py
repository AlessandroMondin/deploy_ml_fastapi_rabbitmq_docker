import base64
import glob
from io import BytesIO

from PIL import Image

for path in glob.glob("data/*.jpeg"):
    buffered = BytesIO()
    image = Image.open(path)
    image.save(buffered, format="JPEG")  # Save image to BytesIO object
    img_str = base64.b64encode(buffered.getvalue()).decode(
        "utf-8"
    )  # Decode bytes to string
    new_path = path.replace(".jpeg", ".txt")
    with open(new_path, "w") as file:
        file.write(img_str)
