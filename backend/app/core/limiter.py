from slowapi import Limiter
from backend.app.dependencies import get_client_ip

# Centralized Limiter configured to safely parse proxy headers using get_client_ip
limiter = Limiter(key_func=get_client_ip)
