import secrets
import string

def generate_secure_string(length: int = 64) -> str:
    """Generate a cryptographically secure random string."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for i in range(length))

def main():
    print("==================================================")
    print("🔒 Akriti PathLab - Secure Keys Generator 🔒")
    print("==================================================")
    print("\nCopy and paste the following keys into your production `.env` file:")
    print("\n# JWT Authentication Secret Key (Required for Token Security)")
    print(f"JWT_SECRET_KEY=\"{generate_secure_string(64)}\"")
    
    print("\n# Password Pepper (Required for Database Password Security)")
    print(f"PASSWORD_PEPPER=\"{generate_secure_string(32)}\"")
    
    print("\n# Allowed CORS Origins (Required for Frontend Access)")
    print("ALLOWED_ORIGINS=\"https://your-production-domain.com\"")
    
    print("\n==================================================")
    print("⚠️  WARNING: Never share these keys or commit them to GitHub.")
    print("==================================================")

if __name__ == "__main__":
    main()
