import pyotp
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils.timezone import now


from django.db.models import F, Q

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

def get_discounted_price(product):
    from AdminProfile.models import Offer
    from AdminProfile.models import Order
    """
    Returns the best discounted price and active offer for a given product.
    Updated to work with ProductTable model.
    """
    current_time = now()
    
    # Query for both product and category offers
    active_offers = Offer.objects.filter(
        Q(
            product=product,
            offer_type='product'
        ) |
        Q(
            category=product.category,
            offer_type='category'
        ),
        is_active=True,
        valid_from__lte=current_time,
        valid_till__gte=current_time
    ).order_by('-discount_value')

    best_offer = None
    final_price = product.sale_Price  
    

    for offer in active_offers:
        # Calculate discounted price
        if offer.discount_type == 'percentage':
            discount_amount = (offer.discount_value / 100) * product.sale_Price
        else:
            discount_amount = offer.discount_value
            
        potential_price = max(product.sale_Price - discount_amount, 0)
        
        # Update if this is the best discount so far
        if potential_price < final_price:
            final_price = potential_price
            best_offer = offer
            
        # If it's a product-specific offer, we can break as it takes precedence
        if offer.offer_type == 'product':
            break

    return {
        'final_price': final_price,
        'original_price': product.sale_Price,
        'saved_amount': product.sale_Price - final_price,
        'offer': best_offer
    }

