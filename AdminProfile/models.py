from django.db import models
from UserProfile.models import UserTable
from decimal import Decimal
from django.core.validators import MinValueValidator
from UserProfile.models import UserTable,Address
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    product = models.ForeignKey("ProductTable", related_name="variances", on_delete=models.CASCADE,null=True,blank=True)
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
        "Calculate the grand total price of the product"
        total = sum(item.total_price for item in self.items.all())
        self.grand_total = round(total,2) # proper decimal rounding
        self.save()
        
    
    @property # @property decorator to make it accessible as cart.total_items instead of calling cart.total_items().
    def total_items(self):
        # getting the total number of items in the cart
        return sum(item.quantity for item in self.items.all())
    
    
    
    
    def add_item(self,product_variant, quantity=1):
        # add items to the cart
        # If it already exists the created flag is False
        item,created = self.items.get_or_create(
            product_variant=product_variant,
            defaults = {'quantity':quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()
        self.update_total()
        return item    
        
        
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
        self.item_price = self.product_variant.product.sale_Price
        self.total_price = round(self.quantity * self.item_price, 2)
        super().save(*args,**kwargs)
        self.cart.update_total()
        
        
    class Meta:
        db_table = 'Cart_item'
        #for preventing duplications
        unique_together = ['cart','product_variant']
        ordering = ['-added_at']
#####################################################################################################################################################################################        
class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELED', 'Canceled'),
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
    
    
    #cancellation details
    canceled_date = models.DateTimeField(null=True,blank=True)
    cancellation_reason = models.TextField(null=True,blank=True)
    
    #return and refund
    return_date = models.DateTimeField(null=True,blank=True)
    return_reason = models.TextField(null = True,blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    refund_date = models.DateTimeField(null=True,blank=True)
    
    #discounts and offers
    
    
    shipping_address = models.ForeignKey(Address,on_delete=models.SET_NULL,null=True,blank=True)
    tracking_id = models.CharField(max_length=100,null=True,blank=True)
    estimated_delivery_date = models.DateField(null=True,blank=True)
    
    #cart and wallet
    cart = models.OneToOneField(Cart,on_delete=models.SET_NULL,null=True)
    
    class Meta:
        ordering = ['-ordered_date']
        db_table = 'Order'
        
    def __str__(self):
        return f"order{self.order_id} - {self.user.username}"
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order,related_name='items', on_delete=models.CASCADE,blank=True,null=True)
    product = models.ForeignKey(Product,on_delete=models.CASCADE,blank=True,null=True)
    variant = models.ForeignKey(VarianceTable,on_delete=models.CASCADE,blank=True,null=True)
    quantity = models.PositiveIntegerField()
    price_per_item = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    #discount informations
    discount_applied = models.BooleanField(default = False)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    discount_prcentage = models.DecimalField(max_digits=5, decimal_places=2,default=0)
    
    #statuses
    is_returned = models.BooleanField(default=False)
    return_date = models.DateTimeField(null=True,blank=True)
    return_reason = models.TextField(null=True,blank=True)
    
    
    class Meta:
        ordering = ['id']
        db_table = 'OrderItem'
        
    def __str__(self):
        return f"{self.quantity}x{self.product.name}in order {self.order.order_id}"
    
    def save(self, *args, **kwargs):
        #calculatting total amount
        self.total_amount = Decimal(self.quantity) * self.price_per_item - self.discount_amount
        super().save(*args, **kwargs)
        
        
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
class Wallet(models.Model):
    wallet_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(UserTable, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wallet of {self.user.username}"

    def has_sufficient_balance(self, amount):
        return self.balance >= Decimal(str(amount))

    def debit(self, amount, description=""):
        if not self.has_sufficient_balance(amount):
            raise ValidationError("Insufficient balance in wallet")
        
        self.balance -= Decimal(str(amount))
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='debit',
            transaction_amount=amount,
            description=description
        )

    def credit(self, amount, description=""):
        self.balance += Decimal(str(amount))
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='credit',
            transaction_amount=amount,
            description=description
        )

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )
    
    transaction_id = models.AutoField(primary_key=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type.title()} of {self.transaction_amount} on {self.created_at.strftime('%Y-%m-%d')}"

# Signal to create wallet when user is created
@receiver(post_save, sender=UserTable)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
        
####################################################################################################################################################################################
class ReturnedItem(models.Model):
    order_item = models.OneToOneField(OrderItem,on_delete=models.CASCADE)
    return_date = models.DateTimeField(auto_now_add=True)
    return_reason = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('PENDING','Pending'),
        ('APPROVED','Approved'),
        ('REJECTED','Rejected')
    ], default='PENDING')
    
    
        