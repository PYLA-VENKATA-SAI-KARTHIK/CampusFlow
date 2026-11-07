"""
CampusFlow — Generate Production RS256 Keypair for Render Environment Variables.
Usage: python backend/scripts/generate_render_keys.py
"""
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    priv_b64 = base64.b64encode(priv_pem).decode("utf-8")
    pub_b64 = base64.b64encode(pub_pem).decode("utf-8")

    print("\n" + "=" * 80)
    print("CAMPUSFLOW PRODUCTION RS256 JWT KEYPAIR (BASE64 FORMAT FOR RENDER)")
    print("=" * 80)
    print("\nCopy these values into your Render backend environment variables:\n")
    print("JWT_PRIVATE_KEY_BASE64:")
    print(priv_b64)
    print("\n" + "-" * 80 + "\n")
    print("JWT_PUBLIC_KEY_BASE64:")
    print(pub_b64)
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    generate()
