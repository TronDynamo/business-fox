#!/usr/bin/env python3
"""Create the owner login from an "Admin setup" GitHub issue opened by the repo owner.

The admin page generates an RSA key pair in the owner's browser and encrypts the private key with
the password the owner chose (PBKDF2-SHA256 + AES-GCM). Only the public key and the encrypted
private key are sent here. This script wraps the vault key with the public key and saves
vault/admin.json. The password never leaves the owner's browser.
"""
import base64, json, os, re, sys
from datetime import datetime, timezone
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

body = os.environ.get("ISSUE_BODY", "")
m = re.search(r"BEGIN-ADMIN-SETUP\s*(\{.*?\})\s*END-ADMIN-SETUP", body, re.S)
if not m:
    sys.exit("No setup block found in the issue.")
req = json.loads(m.group(1))
for k in ("public_key", "enc_private_key", "salt", "iv", "iterations"):
    if k not in req:
        sys.exit(f"Missing {k}")
if int(req["iterations"]) < 300_000:
    sys.exit("Iterations too low")
owner_cfg = json.load(open("tools/delivery_bot.json"))
key = base64.b64decode(os.environ["VAULT_KEY"])
pub = serialization.load_der_public_key(base64.b64decode(req["public_key"]))
wrapped = pub.encrypt(key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
doc = {"v": 2, "kdf": "PBKDF2-SHA256", "iterations": int(req["iterations"]), "salt": req["salt"], "iv": req["iv"],
       "enc_private_key": req["enc_private_key"], "wrapped_key_rsa": base64.b64encode(wrapped).decode(),
       "owner_email_hint": owner_cfg["owner_email"],
       "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
os.makedirs("vault", exist_ok=True)
json.dump(doc, open("vault/admin.json", "w"), indent=2)
print("Owner login saved.")
