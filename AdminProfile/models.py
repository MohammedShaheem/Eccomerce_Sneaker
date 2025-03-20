from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator
from UserProfile.models import UserTable,Address
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
from django.utils.timezone import now
from datetime import datetime, date
from django.utils.timezone import now
from UserProfile.utils import get_discounted_price
from django.utils import timezone
import uuid


class Product(models.Model):
    name = models.CharField(max_length=150, null=False, blank=False)
    description = models.TextField()
    stock_quantity = models.PositiveIntegerField(default=0)  
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=150)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    size = models.PositiveIntegerField(default=7)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'Product'

class Category(models.Model):
    category_name = models.CharField(max_length=150,unique = True,null = False,blank=False)
    description = models.TextField(blank = True, null = True)
    image = models.ImageField(upload_to = 'category_images/',blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_products = models.IntegerField(blank=True,null=True)
    total_earnings = models.DecimalField(max_digits=5, decimal_places=2,blank=True,null=True)
    status = models.BooleanField(default = True)
    is_delete = models.BooleanField(default= False)
    
    
    
    
    def __str__(self):
        return self.category_name

    class Meta:
        db_table = 'Category'
        ordering = ['category_name']





class ProductTable(models.Model):
    name = models.CharField(max_length=50)
    base_price = models.DecimalField(max_digits=7, decimal_places=2)
    product_quantity = models.IntegerField(default=0)
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE,null=True,blank=True)
    sale_Price = models.DecimalField(max_digits=7, decimal_places=2)
    description = models.TextField()
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    Is_deleted = models.BooleanField(default = False)
    Is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
        
    class Meta:
        db_table = 'ProductTable'

######################################################################################################################################################################################
class Size(models.Model):
    size = models.CharField(max_length=50)
    
    
    def __str__(self):
        return self.size
    
    class Meta:
        db_table = 'size'

############################################################################################################################################################################
class Color(models.Model):
    color = models.CharField(max_length=50)
    
    def __str__(self):
        return self.color
    
    class Meta:
        db_table = 'color'
        
###########################################################################################################################################################################        
class VarianceTable(models.Model):
    product = models.ForeignKey(ProductTable, related_name="variances", on_delete=models.CASCADE,null=True,blank=True)
    size = models.ForeignKey("Size",on_delete=models.CASCADE,null=True,blank=True)
    color = models.ForeignKey("Color",on_delete=models.CASCADE,null=True,blank=True)
    Stock_Quantity = models.PositiveIntegerField()
    
    
    def __str__(self):
        return f"{self.product.name} - {self.color.color} - {self.size.size}"
    
    class Meta:
        db_table = 'variance_table'
    
###################################################################################################################################################################   
class Product_Images_Table(models.Model):
    variant = models.ForeignKey(VarianceTable, related_name="images", on_delete=models.CASCADE,null=True,blank=True)
    image = models.ImageField(upload_to="products/")
    
    def __str__(self):
        return f"Image for {self.variant.product.name}"
    
    class Meta:
        db_table = 'Product_Images_Table'
        
############################################################################################################################################################################
class Cart(models.Model):
    user = models.OneToOneField(UserTable,
                                on_delete=models.CASCADE,
                                related_name="cart",
                                null=True,blank=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2,default = 0.00)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Cart for {self.user.username} - Active: {self.is_active}"
    
    def update_total(self):
        #Calculate the grand total price of the product
        total = sum(item.total_price for item in self.items.all())
        self.grand_total = round(total,2) 
        self.save()
        
    
    @property #@property decorator to make it accessible as cart.total_items instead of calling cart.total_items().
    def total_items(self):
        # getting the total number of items in the cart
        return sum(item.quantity for item in self.items.all())
    
    
    
    
    def add_item(self,product_variant, quantity=1):
        #add items to the cart with discounted price
        #if it already exists the created flag is False
        try:
            discount_info = get_discounted_price(product_variant.product)
            item_price = discount_info['final_price']
            item,created = self.items.get_or_create(
                product_variant=product_variant,
                defaults = {
                    'quantity': quantity,
                    'item_price': item_price,
                    'total_price': item_price * quantity
                }
            )
            if not created:
                item.quantity += quantity
                item.total_price = item_price * item.quantity
                item.save()
            self.update_total()
            return item    
        
        except Exception as e:
            print(f"Error in add_item: {str(e)}")
            raise
            
        
    def remove_item(self, product_variant):
        # remove particular item from the cart
        self.items.filter(product_variant=product_variant).delete()
        self.update_total()
        
    def update_item_quantity(self,product_variant,quantity):
        # update item quantity
        if quantity == 0:
            return self.remove_item(product_variant)
        
        item = self.items.filter(product_variant=product_variant).first()
        if item:
            item.quantity = quantity
            item.save()
        self.update_total()
        
        
        
    def clear_cart(self):
        # for clearing all items in the cart
        self.items.all().delete()
        self.update_total()
        
    
    
    
    class Meta:
        db_table = 'Cart_Table'



class CartItem(models.Model):
    
    cart = models.ForeignKey("Cart",
                            on_delete=models.CASCADE,
                            related_name="items")
    product_variant = models.ForeignKey("VarianceTable",
                                        on_delete=models.CASCADE,
                                        related_name = "cart_items")
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    item_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
        )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        # validate model data
        from django.core.exceptions import ValidationError
        
        if self.quantity > self.product_variant.Stock_Quantity:
            raise ValidationError({
                'quantity':f'Only {self.product_variant.Stock_Quantity} items available in stock'
                
            })
    
    def save(self,*args,**kwargs):
        "save with validation and price calculation"
        self.clean()
        self.total_price = round(self.quantity * self.item_price, 2)
        super().save(*args,**kwargs)
        self.cart.update_total()
        
        
    class Meta:
        db_table = 'Cart_item'
        #for preventing duplications
        unique_together = ['cart','product_variant']
        ordering = ['-added_at']
        
############################################################################################################################################################################################
class Coupon(models.Model):
    coupon_name = models.CharField(max_length=100)
    coupon_code = models.CharField(max_length=20)
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=8, decimal_places=2)
    discount_type = models.CharField(max_length=10, choices=[('fixed', 'Fixed'), ('percent', 'Percentage')])
    valid_from = models.DateTimeField()
    valid_till = models.DateTimeField()
    max_uses = models.IntegerField(default=1)  # How many times this coupon can be used globally
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    # Track who has used this coupon
    used_by = models.ManyToManyField(UserTable, through='CouponUsage', related_name='used_coupons')

    def __str__(self):
        return f"{self.coupon_name} ({self.coupon_code})"
        
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and 
            not self.is_deleted and 
            self.valid_from <= now and 
            self.valid_till >= now
        )
        
    @property
    def total_uses(self):
        return self.couponusage_set.count()
        
    def can_use(self):
        return self.total_uses < self.max_uses if self.max_uses > 0 else True
    
    
    def apply(self, user, cart_total):
        #validate and calculate discount for a coupon
        if not self.is_active or self.is_deleted:
            return None, "This coupon is not active"
        if not self.is_valid():
            return None, "This coupon is not valid or has expired"
        if CouponUsage.objects.filter(user=user, coupon=self).exists():
            return None, "You have already used this coupon"
        if not self.can_use():
            return None, "This coupon has reached its maximum usage limit"
        if cart_total < self.min_purchase_amount:
            return None, f"This coupon requires a minimum purchase of ₹{self.min_purchase_amount}"
        
        if self.discount_type == 'fixed':
            discount = min(self.discount, cart_total)
        else:
            discount = min((cart_total * self.discount / 100), cart_total)
        return discount, None
    class Meta:
        #Add a conditional unique constraint
        constraints = [
            models.UniqueConstraint(
                fields=['coupon_code'],
                condition=models.Q(is_deleted=False),  # Only enforce uniqueness on non-deleted coupons
                name='unique_active_coupon_code'
            )
        ]

class CouponUsage(models.Model):
    user = models.ForeignKey(UserTable, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        #each user can use a coupon only once
        unique_together = ['user', 'coupon']
        
    def __str__(self):
        return f"{self.user.username} used {self.coupon.coupon_code} on {self.used_at.strftime('%Y-%m-%d')}"
    
    
    
class Offer(models.Model):
    OFFER_TYPE_CHOICES = [
        ('product', 'Product Offer'),
        ('category', 'Category Offer'),
    ]
    
    DISCOUNT_TYPE_CHOICES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage')
    ]
    
    offer_title = models.CharField(max_length=255)
    offer_type = models.CharField(max_length=10, choices=OFFER_TYPE_CHOICES)
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Enter percentage (0-100) or fixed amount"
    )
    discount_type = models.CharField(
        max_length=10, 
        choices=DISCOUNT_TYPE_CHOICES, 
        default='percentage'
    )
    valid_from = models.DateField(default=now)  
    valid_till = models.DateField()
    offer_description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

    product = models.ForeignKey(
        ProductTable, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        related_name='offers'
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        related_name='offers'
    )

    class Meta:
        indexes = [
            models.Index(fields=['offer_type', 'is_active', 'valid_from', 'valid_till']),
        ]

    def clean(self):
        if self.offer_type == 'product' and not self.product:
            raise ValidationError("Product must be selected for product offer type")
        if self.offer_type == 'category' and not self.category:
            raise ValidationError("Category must be selected for category offer type")
            
        if self.discount_type == 'percentage' and (self.discount_value < 0 or self.discount_value > 100):
            raise ValidationError("Percentage discount must be between 0 and 100")
            
        # Update validation for date fields
        if self.valid_till and self.valid_from and self.valid_till <= self.valid_from:
            raise ValidationError("End date must be after start date")

        # Validate that dates are not in the past
        today = date.today()
        if self.valid_from < today:
            raise ValidationError("Start date cannot be in the past")

    @property
    def is_valid(self):
        current_date = date.today()
        
        # Handle date conversion
        valid_from_date = self.valid_from
        valid_till_date = self.valid_till
        
        if isinstance(self.valid_from, type(datetime)):
            valid_from_date = self.valid_from.date()
        if isinstance(self.valid_till, type(datetime)):
            valid_till_date = self.valid_till.date()
        
        return (
            self.is_active and 
            valid_from_date <= current_date and 
            valid_till_date >= current_date
        )

    @property
    def status_display(self):
        current_date = date.today()
        
        if not self.is_active:
            return 'Inactive'
        
        # Handle date conversion
        valid_from_date = self.valid_from
        valid_till_date = self.valid_till
        
        if isinstance(self.valid_from, type(datetime)):
            valid_from_date = self.valid_from.date()
        if isinstance(self.valid_till, type(datetime)):
            valid_till_date = self.valid_till.date()
        
        if valid_from_date > current_date:
            return 'Scheduled'
        elif valid_till_date < current_date:
            return 'Expired'
        return 'Active'

#####################################################################################################################################################################################        
def generate_transaction_id():
   timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
   unique_id = uuid.uuid4().hex[:6]
   return f"TXN-{timestamp}-{unique_id}" 

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELED', 'Canceled'),
        ('PARTIALLY_RETURNED', 'Partially Returned'),
        ('RETURNED', 'Returned')
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded')
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('CARD', 'Credit/Debit Card'),
        ('UPI', 'UPI'),
        ('WALLET', 'Wallet'),
        ('COD', 'Cash on Delivery')
    )
    
    RETURN_STATUS_CHOICES = (
        ('NONE','None'),
        ('REQUESTED','Requested'),
        ('APPROVED','Approved'),
        ('REJECTED','Rejected')
    )
    
    
    order_id = models.CharField(max_length=50, unique=True)#custom order id
    user = models.ForeignKey(UserTable,on_delete=models.CASCADE,related_name='orders',null=True,blank=True)
    ordered_date = models.DateTimeField(auto_now_add=True)
    
    #status and payments
    order_status = models.CharField(max_length=20, 
                                    choices=STATUS_CHOICES,
                                    default='PENDING')
    payment_status = models.CharField(max_length=20,
                                      choices=PAYMENT_STATUS_CHOICES,
                                      default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2) 
    
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True, editable=False)
    
    #cancellation details
    canceled_date = models.DateTimeField(null=True,blank=True)
    cancellation_reason = models.TextField(null=True,blank=True)
    
    #return and refund
    return_date = models.DateTimeField(null=True,blank=True)
    return_reason = models.TextField(null = True,blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    refund_date = models.DateTimeField(null=True,blank=True)
    
    return_status = models.CharField(max_length=50,choices=RETURN_STATUS_CHOICES,default='NONE')
    
    
    
    tracking_id = models.CharField(max_length=100,null=True,blank=True)
    estimated_delivery_date = models.DateField(null=True,blank=True)
    
    #cart 
    cart = models.OneToOneField(Cart,on_delete=models.SET_NULL,null=True)
    
    offer_applied = models.BooleanField(default = False)
    coupon_applied = models.BooleanField(default = False)
    
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    
    
    class Meta:
        ordering = ['-ordered_date']
        db_table = 'Order'
    
    def save(self,*args, **kwargs):
        if not self.transaction_id and self.payment_method in ['UPI','WALLET']:
            while True:
                new_id = generate_transaction_id()
                if not Order.objects.filter(transaction_id=new_id).exists():
                    self.transaction_id = new_id
                    break
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"order{self.order_id} - {self.user.username}"
    

class OrderItem(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELED', 'Canceled'),
        ('PARTIALLY_RETURNED', 'Partially Returned'),
        ('RETURNED', 'Returned'),
        
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded')
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('CARD', 'Credit/Debit Card'),
        ('UPI', 'UPI'),
        ('WALLET', 'Wallet'),
        ('COD', 'Cash on Delivery')
    )
    
    RETURN_STATUS_CHOICES = (
        ('NONE','None'),
        ('REQUESTED','Requested'),
        ('APPROVED','Approved'),
        ('REJECTED','Rejected')
    )
    order = models.ForeignKey(Order,related_name='items', on_delete=models.CASCADE,blank=True,null=True)
    product = models.ForeignKey(ProductTable,on_delete=models.CASCADE,blank=True,null=True)
    variant = models.ForeignKey(VarianceTable,on_delete=models.CASCADE,blank=True,null=True)
    quantity = models.PositiveIntegerField()
    price_per_item = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    item_status = models.CharField(max_length=20, 
                                    choices=STATUS_CHOICES,
                                    default='PENDING')
    item_payment_status = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES,default = 'PENDING')
    item_return_status = models.CharField(max_length=50,choices=RETURN_STATUS_CHOICES,default='NONE')
    
    #discount informations
    discount_applied = models.BooleanField(default = False)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    discount_prcentage = models.DecimalField(max_digits=5, decimal_places=2,default=0)
    
    #statuses
    is_returned = models.BooleanField(default=False)
    return_date = models.DateTimeField(null=True,blank=True)
    return_reason = models.TextField(null=True,blank=True)
    is_canceled = models.BooleanField(default=False)
    cancelation_reason = models.TextField(null=True,blank=True)
    offer = models.ForeignKey(Offer,on_delete=models.SET_NULL,null=True,blank=True)
    
    
    class Meta:
        ordering = ['id']
        db_table = 'OrderItem'
        
    def __str__(self):
        return f"{self.quantity}x{self.product.name}in order {self.order.order_id}"
    
    def save(self, *args, **kwargs):
        #calculatting total amount
        self.total_amount = Decimal(self.quantity) * self.price_per_item - self.discount_amount
        super().save(*args, **kwargs)

class ReturnRequest(models.Model):
    RETURN_STATUS_CHOICES = (
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='return_request')
    user = models.ForeignKey(UserTable,on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=50,choices=RETURN_STATUS_CHOICES,default='REQUESTED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes  = models.TextField(blank=True,null=True)
    
    def __str__(self):
        return f"Return Request #{self.id} for Order #{self.order.order_id}"
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'ReturnRequest'
        
class ReturnRequestItem(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='return_request_items')
    
    def __str__(self):
        return f"Return Request Item for {self.order_item.product.name} in Request #{self.return_request.id}"
    
    class Meta:
        db_table = 'ReturnRequestItem'
    
        
class Wishilist(models.Model):
    user = models.ForeignKey(UserTable, related_name='wishilist', on_delete=models.CASCADE,null=True,blank=True)
    product = models.ForeignKey(ProductTable, related_name="Wishilisted_by", on_delete=models.CASCADE,null=True,blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'Wishilist'
        #ensuring a user can't add the same product multiple times
        unique_together = ['user','product']
        ordering = ['-added_at']
        
        
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
    



#############################################################################################################################################################################################
from django.core.exceptions import ValidationError
from django.db import models
from decimal import Decimal

class Wallet(models.Model):
    wallet_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(UserTable, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wallet of {self.user.username}"

    def has_sufficient_balance(self, amount):
        return self.balance >= Decimal(str(amount))

    def debit(self, amount, description="", transaction_category='WALLET_OPERATION'):
        if not self.has_sufficient_balance(amount):
            raise ValidationError("Insufficient balance in wallet")
        
        self.balance -= Decimal(str(amount))
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='debit',
            transaction_category=transaction_category,
            transaction_amount=amount,
            description=description
        )

    def credit(self, amount, description="", order=None, transaction_category='WALLET_OPERATION'):
        self.balance += Decimal(str(amount))
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='credit',
            transaction_category=transaction_category,
            transaction_amount=amount,
            description=description,
            order=order
        )

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )
    
    TRANSACTION_CATEGORIES = (
        ('WALLET_OPERATION', 'Wallet Operation'),
        ('ORDER_CANCELLATION', 'Order Cancellation'),
        ('ORDER_RETURN', 'Order Return'),
    )
    
    transaction_id = models.AutoField(primary_key=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    transaction_category = models.CharField(
        max_length=20,
        choices=TRANSACTION_CATEGORIES,
        default='WALLET_OPERATION'
    )
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type.title()} ({self.get_transaction_category_display()}) of {self.transaction_amount} on {self.created_at.strftime('%Y-%m-%d')}"
# Signal to create wallet when user is created
@receiver(post_save, sender=UserTable)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
        
####################################################################################################################################################################################
class OrderAddress(models.Model):
    order = models.OneToOneField(Order,on_delete=models.CASCADE,related_name='order_address')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=254)
    address_type = models.TextField()
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    house_name = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    def __str__(self):
        return f"Address for Order {self.order.order_id}"

    class Meta:
        db_table = 'OrderAdress'
        verbose_name = "Order Address"
        verbose_name_plural = "Order Addresses"
    

#########################################################################################################################################################################################


###############################################################################################################################################################################################################################################
