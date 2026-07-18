import sys
import os
import bcrypt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.app.core.security import hash_password, verify_password, validate_password_policy
from backend.app.config import settings

assert settings.PASSWORD_PEPPER != "", "PASSWORD_PEPPER is empty!"
print("✅ Pepper is loaded securely.")

pass1 = hash_password("MySecurePassword123")
pass2 = hash_password("MySecurePassword123")
assert pass1 != pass2, "Hashes are identical! Automatic salt failed."
assert pass1.startswith("$"), "Hash is not Argon2id!"
print("✅ Automatic Salt is working.")

is_valid, needs_rehash = verify_password("MySecurePassword123", pass1)
assert is_valid is True, "Verification failed!"
assert needs_rehash is False, "New hash requested rehash!"
print("✅ Verification works securely.")

is_valid, _ = verify_password("WrongPassword123", pass1)
assert is_valid is False, "Wrong password verified successfully!"
print("✅ Wrong password rejected.")

old_hash = bcrypt.hashpw(b"OldUserPassword", bcrypt.gensalt()).decode("utf-8")
is_valid, needs_rehash = verify_password("OldUserPassword", old_hash)
assert is_valid is True, "Bcrypt verification failed!"
assert needs_rehash is True, "Bcrypt verification did not flag for migration!"
print("✅ Bcrypt migration trigger works perfectly.")

assert validate_password_policy("WeakPass") == False, "Weak password allowed!"
assert validate_password_policy("StrongPassword123!") == True, "Strong password rejected!"
print("✅ Password Policy works.")

print("\n🚀 ALL SECURITY TESTS PASSED SUCCESSFULLY.")
