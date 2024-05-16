import logging
import torch
import replicate
import base64
import os
import requests
from mmtafrica.mmtafrica import load_params, translate
from huggingface_hub import hf_hub_download


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


language_map = {
    "English": "en",
    "Swahili": "sw",
    "Fon": "fon",
    "Igbo": "ig",
    "Kinyarwanda": "rw",
    "Xhosa": "xh",
    "Yoruba": "yo",
    "French": "fr",
}

# Load parameters and model from checkpoint
checkpoint = hf_hub_download(
    repo_id="chrisjay/mmtafrica", filename="mmt_translation.pt"
)
device = "gpu" if torch.cuda.is_available() else "cpu"
params = load_params({"checkpoint": checkpoint, "device": device})


def get_translation(source_language, target_language, source_sentence=None):
    """
    This takes a sentence and gets the translation.
    """

    source_language_ = language_map[source_language]
    target_language_ = language_map[target_language]

    try:
        pred = translate(
            params,
            source_sentence,
            source_lang=source_language_,
            target_lang=target_language_,
        )
        if pred == "":
            return f"Could not find translation"
        else:
            return pred
    except Exception as error:
        return f"Issue with translation: \n {error}"


"""## Text-to-Image 🗣"""


def generate_image_from_text_replicate(prompt):
    input = {"prompt": prompt, "scheduler": "K_EULER"}

    output = replicate.run(
        "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
        input=input,
    )
    return output[0]
    # => ["https://replicate.delivery/pbxt/sWeZFZou6v3CPKuoJbqX46u...


def generate_image_from_text_stability(prompt, size="medium", samples=1):
    """
    Generate an image from text using the Stability AI API.

    Args:
        prompt (str): The text prompt for generating the image.
        size (str, optional): The size of the image. Default is 'medium'.
            Available options: 'small', 'medium', 'big', 'landscape', 'portrait'.
        samples (int, optional): Number of samples to generate. Default is 1.
        steps (int, optional): Number of steps for generation. Default is 30.

    Returns:
        list of bytes: List of image data in bytes format.
    """
    engine_id = "stable-diffusion-v1-6"
    api_host = os.getenv("API_HOST", "https://api.stability.ai")
    api_key = "sk-FIg0J97YXf92aDudJrSsIIXsdWsnnKaT5mUdRS6REIZnqCoM"

    if api_key is None:
        raise Exception("Missing Stability API key.")

    sizes = {
        "small": {"height": 512, "width": 512},
        "medium": {"height": 1024, "width": 1024},
        "big": {"height": 1536, "width": 1536},
        "landscape": {"height": 768, "width": 1024},
        "portrait": {"height": 1024, "width": 768},
    }

    if size not in sizes:
        try:
            generate_image_from_text_replicate(prompt)
        except Exception as e:
            raise ValueError(
                "Invalid size. Please choose from: small, medium, big, landscape, portrait."
            )

    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": sizes[size]["height"],
            "width": sizes[size]["width"],
            "samples": samples,
            "steps": 30,
        },
    )

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()

    images = []
    for i, image in enumerate(data["artifacts"]):
        images.append(base64.b64decode(image["base64"]))

    return images


# # Example usage:
# images = generate_image_from_text("A lighthouse on a cliff", size='small')

# # Save each image to the root directory
# for i, image_data in enumerate(images):
#     image = Image.open(io.BytesIO(image_data))
#     image.save(f"txt2img_{i}.png")


"""## Text-to-Speech 🗣"""

CHUNK_SIZE = 1024


def text_to_speech(text, voice_id, api_key, output_file):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

        logging.info(f"Audio file '{output_file}' generated successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
