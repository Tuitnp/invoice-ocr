"""Download the pinned Apache-2.0 OpenThai runtime and weights."""
from pathlib import Path
import urllib.request
import hashlib
import json
REV='39fa41bdd49f067ba41b1d9de79c06ab506d67d4'
ROOT=Path(__file__).resolve().parents[1]
FILES=['NOTICE','config.json','det.onnx','rec.onnx','rec_dict.txt','runtime/__init__.py','runtime/line_engine.py','runtime/thai_norm.py']
checks=json.loads((ROOT/'model-checksums.json').read_text())
for name in FILES:
 target=ROOT/'models'/name
 target.parent.mkdir(parents=True,exist_ok=True)
 data=urllib.request.urlopen(f'https://huggingface.co/iapp/OpenThai2.0-OCR-Text/resolve/{REV}/{name}',timeout=120).read()
 if hashlib.sha256(data).hexdigest()!=checks[name]: raise RuntimeError(f'Checksum mismatch: {name}')
 target.write_bytes(data)
 print(name)
