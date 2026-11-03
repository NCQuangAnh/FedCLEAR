import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gate_D"))  # logs live under gate_D
import json,glob,collections
C=['label','true']+[f'{d}_{c}' for d in 'gze' for c in ('py','pred','pmax','H','sumsq','pnn')]
IX={c:i for i,c in enumerate(C)}
K={"oxford_pets":37,"dtd":47,"caltech101":100}
def runs(ds,sc,arm="none"):
    return sorted(glob.glob(f"**/{ds}_D_{sc}_{arm}/**/diag_samples_seed_*.json",recursive=True))
def load(f):
    out=collections.defaultdict(dict)  # round -> client -> rows
    for rec in json.load(open(f)):
        out[rec['round']][rec['client']]=rec['rows']
    return out
