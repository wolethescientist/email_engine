import secrets
import base64

# Generate a secure 32-byte (256-bit) key and Base64-encode it
key_bytes = secrets.token_bytes(32)
key_b64 = base64.b64encode(key_bytes).decode("ascii")

print(key_b64)
