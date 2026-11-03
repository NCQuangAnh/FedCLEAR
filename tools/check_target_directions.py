"""Pre-check for target-direction residualisation (gate L, arm L_tdr). CPU, no images, ~minutes.

The idea only works if "the direction in prompt space that makes class c steal other classes"
is a different direction for different c. CoOp's prompt here is ONE generic context of 4 tokens
x 512 shared by every class, so those directions could all be nearly the same vector -- in
which case cutting the target's direction would cut general learning with it, and the arm is
not worth a GPU hour.

phi_c(P) = mean over probes j != c of softmax_j(c): how much probability the zero-shot text
embedding of every OTHER class assigns to class c under prompt P. The zero-shot embeddings
stand in for images, which the server does not have. Only mass from other classes counts, so a
client that learned class c from real images of c is not what this direction measures -- the
label-flip attack is exactly "images of other classes -> c".

d_c = grad_P phi_c. Reported: pairwise cosine between the d_c, raw and after removing the
component every class shares (the mean direction), at two prompt states.

Usage:  python tools/check_target_directions.py
"""
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "flip"))
from flcore.models.clip import clip                      # noqa: E402
from flcore.models.clip.clip import load_clip_to_cpu      # noqa: E402
from flcore.models.text.encoder import TextEncoder        # noqa: E402

DTD = ["banded", "blotchy", "braided", "bubbly", "bumpy", "chequered", "cobwebbed", "cracked",
       "crosshatched", "crystalline", "dotted", "fibrous", "flecked", "freckled", "frilly",
       "gauzy", "grid", "grooved", "honeycombed", "interlaced", "knitted", "lacelike", "lined",
       "marbled", "matted", "meshed", "paisley", "perforated", "pitted", "pleated", "polka-dotted",
       "porous", "potholed", "scaly", "smeared", "spiralled", "sprinkled", "stained", "stratified",
       "striped", "studded", "swirly", "veined", "waffled", "woven", "wrinkled", "zigzagged"]
PETS = ["Abyssinian", "American Bulldog", "American Pit Bull Terrier", "Basset Hound", "Beagle",
        "Bengal", "Birman", "Bombay", "Boxer", "British Shorthair", "Chihuahua", "Egyptian Mau",
        "English Cocker Spaniel", "English Setter", "German Shorthaired", "Great Pyrenees",
        "Havanese", "Japanese Chin", "Keeshond", "Leonberger", "Maine Coon",
        "Miniature Pinscher", "Newfoundland", "Persian", "Pomeranian", "Pug", "Ragdoll",
        "Russian Blue", "Saint Bernard", "Samoyed", "Scottish Terrier", "Shiba Inu", "Siamese",
        "Sphynx", "Staffordshire Bull Terrier", "Wheaten Terrier", "Yorkshire Terrier"]


def directions(model, enc, names, init):
    names = [n.replace("_", " ") for n in names]
    n_ctx = 4
    tok = torch.cat([clip.tokenize("X " * n_ctx + n + ".") for n in names])
    with torch.no_grad():
        emb = model.token_embedding(tok).float()
        zs = model.encode_text(torch.cat([clip.tokenize(f"a photo of a {n}.") for n in names])).float()
        zs = zs / zs.norm(dim=-1, keepdim=True)
    if init == "random":
        torch.manual_seed(0)
        ctx0 = torch.randn(n_ctx, emb.shape[-1]) * 0.02
    else:   # the embedding of "a photo of a" -- a stand-in for a prompt that has learned something
        with torch.no_grad():
            ctx0 = model.token_embedding(clip.tokenize("a photo of a"))[0, 1:1 + n_ctx].float()
    ctx = ctx0.clone().requires_grad_(True)
    prompts = torch.cat([emb[:, :1], ctx.unsqueeze(0).expand(len(names), -1, -1),
                         emb[:, 1 + n_ctx:]], dim=1)
    t = enc(prompts, tok).float()
    t = t / t.norm(dim=-1, keepdim=True)
    p = (100.0 * zs @ t.t()).softmax(dim=-1)              # rows: probes, cols: classes
    C = len(names)
    off = 1.0 - torch.eye(C)
    phi = (p * off).sum(0) / (C - 1)                      # mass other classes send to column c
    ds = []
    for c in range(C):
        g, = torch.autograd.grad(phi[c], ctx, retain_graph=True)
        ds.append(g.reshape(-1))
    return torch.stack(ds)


def report(tag, D):
    Dn = D / D.norm(dim=1, keepdim=True)
    cos = Dn @ Dn.t()
    iu = torch.triu_indices(len(D), len(D), 1)
    raw = cos[iu[0], iu[1]]
    Dc = D - D.mean(0, keepdim=True)                      # remove what every class shares
    Dc = Dc / Dc.norm(dim=1, keepdim=True)
    cc = (Dc @ Dc.t())[iu[0], iu[1]]
    shared = (D.mean(0).norm() / D.norm(dim=1).mean()).item()
    print(f"  {tag:22s} raw cos: mean {raw.mean():+.3f}, >0.9 {100*(raw>0.9).float().mean():5.1f}% | "
          f"after removing shared part: mean {cc.mean():+.3f}, max {cc.max():+.3f} | "
          f"shared part = {100*shared:4.1f}% of a direction's length")


def main():
    model = load_clip_to_cpu("RN50", zero_shot=True).float().eval()
    enc = TextEncoder(model)
    for name, names in (("DTD", DTD), ("OxfordPets", PETS)):
        print(name, f"({len(names)} classes)")
        for init in ("random", "a photo of a"):
            report(f"prompt = {init}", directions(model, enc, names, init))


if __name__ == "__main__":
    main()
