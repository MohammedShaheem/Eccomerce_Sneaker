import pyotp
from datetime import datetime, timedelta
from django.core.cache import cache

def generate_otp(email):
    """Generate OTP and store in cache with email as key"""
    # Generate a random secret key
    secret = pyotp.random_base32()
    
    # Create TOTP object with 5 minutes validity
    totp = pyotp.TOTP(secret, interval=300)
    otp = totp.now()
    
    # Store OTP in cache with 5 minutes expiry
    cache.set(f'email_otp_{email}', otp, timeout=300)
    
    return otp

def verify_otp(email, otp):
    """Verify OTP from cache"""
    stored_otp = cache.get(f'email_otp_{email}')
    if stored_otp and str(stored_otp) == str(otp):
        # Delete OTP from cache after successful verification
        cache.delete(f'email_otp_{email}')
        return True
    return False