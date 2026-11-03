# Reconstructed loader for FLIP. The published FLIP repository (0-ml/flip @ ec3a848)
# ships this file empty, while server_base.py, text/prompt.py, ProGrad.py and several
# model files import `load_clip_to_cpu`, `tokenize` and `clip.*` from it.
#
# Adapted from the official OpenAI CLIP loader (https://github.com/openai/CLIP,
# clip/clip.py, MIT License, Copyright (c) 2021 OpenAI) and from the
# `load_clip_to_cpu` helper used by CoOp / MaPLe. FLIP's own `model.py` expects
# `build_model(state_dict, design_details)`, so the loader passes design_details through.
import hashlib
import os
import urllib.request
import warnings
from typing import List, Union

import torch
from PIL import Image
from torchvision.transforms import CenterCrop, Compose, Normalize, Resize, ToTensor
from tqdm import tqdm

from .model import build_model
from .simple_tokenizer import SimpleTokenizer as _Tokenizer

try:
    from torchvision.transforms import InterpolationMode
    BICUBIC = InterpolationMode.BICUBIC
except ImportError:
    BICUBIC = Image.BICUBIC


__all__ = ["available_models", "load", "tokenize", "load_clip_to_cpu"]
_tokenizer = _Tokenizer()

_MODELS = {
    "RN50": "https://openaipublic.azureedge.net/clip/models/afeb0e10f9e5a86da6080e35cf09123aca3b358a0c3e3b6c78a7b63bc04b6762/RN50.pt",
    "RN101": "https://openaipublic.azureedge.net/clip/models/8fa8567bab74a42d41c5915025a8e4538c3bdbe8804a470a72f30b0d94fab599/RN101.pt",
    "RN50x4": "https://openaipublic.azureedge.net/clip/models/7e526bd135e493cef0776de27d5f42653e6b4c8bf9e0f653bb11773263205fdd/RN50x4.pt",
    "RN50x16": "https://openaipublic.azureedge.net/clip/models/52378b407f34354e150460fe41077663dd5b39c54cd0bfd2b27167a4a06ec9aa/RN50x16.pt",
    "RN50x64": "https://openaipublic.azureedge.net/clip/models/be1cfb55d75a9666199fb2206c106743da0f6468c9d327f3e0d0a543a9919d9c/RN50x64.pt",
    "ViT-B/32": "https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt",
    "ViT-B/16": "https://openaipublic.azureedge.net/clip/models/5806e77cd80f8b59890b7e101eabd078d9fb84e6937f9e85e4ecb61988df416f/ViT-B-16.pt",
    "ViT-L/14": "https://openaipublic.azureedge.net/clip/models/b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836/ViT-L-14.pt",
    "ViT-L/14@336px": "https://openaipublic.azureedge.net/clip/models/3035c92b350959924f9f00213499208652fc7ea050643e8b385c2dac08641f02/ViT-L-14-336px.pt",
}

# Where downloaded weights are cached. On Kaggle, point FLIP_CLIP_CACHE at an attached
# dataset that already holds the .pt files to avoid re-downloading every session.
DEFAULT_CACHE = os.environ.get("FLIP_CLIP_CACHE", os.path.expanduser("~/.cache/clip"))


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, root: str = DEFAULT_CACHE) -> str:
    os.makedirs(root, exist_ok=True)
    filename = os.path.basename(url)
    expected_sha256 = url.split("/")[-2]
    download_target = os.path.join(root, filename)

    if os.path.exists(download_target) and not os.path.isfile(download_target):
        raise RuntimeError(f"{download_target} exists and is not a regular file")

    if os.path.isfile(download_target):
        if _sha256(download_target) == expected_sha256:
            return download_target
        warnings.warn(f"{download_target} exists, but the SHA256 checksum does not match; re-downloading the file")

    with urllib.request.urlopen(url) as source, open(download_target, "wb") as output:
        with tqdm(total=int(source.info().get("Content-Length")), ncols=80, unit="iB",
                  unit_scale=True, unit_divisor=1024) as loop:
            while True:
                buffer = source.read(8192)
                if not buffer:
                    break
                output.write(buffer)
                loop.update(len(buffer))

    if _sha256(download_target) != expected_sha256:
        raise RuntimeError("Model has been downloaded but the SHA256 checksum does not match")
    return download_target


def _convert_image_to_rgb(image):
    return image.convert("RGB")


def _transform(n_px):
    return Compose([
        Resize(n_px, interpolation=BICUBIC),
        CenterCrop(n_px),
        _convert_image_to_rgb,
        ToTensor(),
        Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)),
    ])


def available_models() -> List[str]:
    """Returns the names of available CLIP models."""
    return list(_MODELS.keys())


def _read_state_dict(name: str, download_root: str = None) -> dict:
    if name in _MODELS:
        model_path = _download(_MODELS[name], download_root or DEFAULT_CACHE)
    elif os.path.isfile(name):
        model_path = name
    else:
        raise RuntimeError(f"Model {name} not found; available models = {available_models()}")

    with open(model_path, "rb") as opened_file:
        try:
            # OpenAI checkpoints are TorchScript archives
            return torch.jit.load(opened_file, map_location="cpu").eval().state_dict()
        except RuntimeError:
            opened_file.seek(0)
            return torch.load(opened_file, map_location="cpu")


def load_clip_to_cpu(backbone_name: str, zero_shot: bool = False, design_details: dict = None,
                     download_root: str = None):
    """Build FLIP's CLIP model on CPU.

    zero_shot=True builds a plain CLIP (no MaPLe-style deep prompts), which is what
    FLIP's callers use for teacher / zero-shot text features.
    """
    state_dict = _read_state_dict(backbone_name, download_root)
    if zero_shot:
        design_details = None
    return build_model(state_dict, design_details)


def load(name: str, device: Union[str, torch.device] = "cpu", download_root: str = None):
    """Non-JIT variant of clip.load kept for API compatibility."""
    model = build_model(_read_state_dict(name, download_root), None).to(device)
    if str(device) == "cpu":
        model.float()
    return model, _transform(model.visual.input_resolution)


def tokenize(texts: Union[str, List[str]], context_length: int = 77, truncate: bool = False) -> torch.LongTensor:
    """Tokenize text(s) into a [N, context_length] LongTensor (CoOp-style dtype)."""
    if isinstance(texts, str):
        texts = [texts]

    sot_token = _tokenizer.encoder["<|startoftext|>"]
    eot_token = _tokenizer.encoder["<|endoftext|>"]
    all_tokens = [[sot_token] + _tokenizer.encode(text) + [eot_token] for text in texts]
    result = torch.zeros(len(all_tokens), context_length, dtype=torch.long)

    for i, tokens in enumerate(all_tokens):
        if len(tokens) > context_length:
            if truncate:
                tokens = tokens[:context_length]
                tokens[-1] = eot_token
            else:
                raise RuntimeError(f"Input {texts[i]} is too long for context length {context_length}")
        result[i, :len(tokens)] = torch.tensor(tokens)

    return result
