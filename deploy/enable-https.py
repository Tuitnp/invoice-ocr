#!/usr/bin/python3
"""Issue HTTPS only once public DNS points at this host. No zone files changed."""
import json
from pathlib import Path
import subprocess
import urllib.request
DOMAIN='invoice.tanapat.dev'
EXPECTED_IP='213.35.98.114'
marker=Path('/var/lib/invoice-ocr/https-ready')
if marker.exists():
 subprocess.run(['systemctl','disable','--now','invoice-ocr-https.timer'],check=True)
 raise SystemExit(0)
try:
 req=urllib.request.Request(f'https://dns.google/resolve?name={DOMAIN}&type=A',headers={'Accept':'application/dns-json'})
 with urllib.request.urlopen(req,timeout=15) as response: dns=json.load(response)
 addresses={a['data'] for a in dns.get('Answer',[]) if a['type']==1}
 if addresses!={EXPECTED_IP}:
  print(f'Waiting for {DOMAIN} A record to point to {EXPECTED_IP}',flush=True)
  raise SystemExit(0)
except (OSError,ValueError) as exc:
 print(f'DNS check unavailable: {type(exc).__name__}',flush=True)
 raise SystemExit(0)
subprocess.run(['/usr/bin/certbot','--nginx','--non-interactive','--agree-tos','--redirect','--keep-until-expiring','-d',DOMAIN],check=True,timeout=180)
marker.parent.mkdir(parents=True,exist_ok=True)
marker.touch()
subprocess.run(['systemctl','disable','--now','invoice-ocr-https.timer'],check=True)
