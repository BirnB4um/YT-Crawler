
from huggingface_hub import snapshot_download
import urllib.request
import os

base_path = "../data/models/"
if not os.path.exists(base_path):
    os.makedirs(base_path, exist_ok=True)

model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
model_path = os.path.join(base_path, model_name.split("/")[-1])
if not os.path.exists(model_path):
    print(f"Downloading {model_name} model...")
    snapshot_download(model_name, local_dir=model_path)
else:
    print(f"Model {model_name} already exists.")

# download lid.176.ftz fasttext model for language detection
ft_model_path = os.path.join(base_path, "lid.176.ftz")
if not os.path.exists(ft_model_path):
    print("Downloading lid.176.ftz fasttext model...")
    ft_model_url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz"
    urllib.request.urlretrieve(ft_model_url, ft_model_path)
else:
    print("Fasttext model lid.176.ftz already exists.")