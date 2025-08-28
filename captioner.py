from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import torch
from PIL import Image
from io import BytesIO

model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
feature_extractor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.config.pad_token_id = model.config.eos_token_id
model.to(device)
model.eval()

gen_kwargs = {"max_length": 16, "num_beams": 4}

def caption_image(image_bytes: bytes) -> str:
    """
    Accept raw image bytes and return a single caption string.
    """
    img = Image.open(BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    pixel_values = feature_extractor(images=[img], return_tensors="pt").pixel_values.to(device)

    with torch.no_grad():
        output_ids = model.generate(pixel_values, **gen_kwargs)

    caption = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
    return caption
