from transformers import DonutProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
import re
import json

# ---------------------------
# Load model
# ---------------------------
model_name = "naver-clova-ix/donut-base"

print("Loading Donut...")

processor = DonutProcessor.from_pretrained(model_name)
model = VisionEncoderDecoderModel.from_pretrained(model_name)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

print("Model loaded!")

# ---------------------------
# Load image
# ---------------------------
image = Image.open("1.png").convert("RGB")

# ---------------------------
# Prompt (IMPORTANT)
# ---------------------------
task_prompt = "List all numbers visible in the chart. Do not explain."

# Prepare input
pixel_values = processor(image, return_tensors="pt").pixel_values.to(device)
decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids.to(device)

# ---------------------------
# Generate output
# ---------------------------
outputs = model.generate(
    pixel_values,
    decoder_input_ids=decoder_input_ids,
    max_length=512,
    pad_token_id=processor.tokenizer.pad_token_id,
    eos_token_id=processor.tokenizer.eos_token_id,
)

# Decode
result = processor.batch_decode(outputs, skip_special_tokens=True)[0]

print("\nRAW OUTPUT:\n", result)

# ---------------------------
# Try to extract JSON
# ---------------------------
try:
    json_str = re.search(r"\{.*\}", result, re.DOTALL).group(0)
    parsed = json.loads(json_str)
    print("\nPARSED JSON:\n", json.dumps(parsed, indent=2))
except:
    print("\nCould not parse structured JSON. Needs prompt tuning.")
