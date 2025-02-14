from django.db import models
from UserProfile.models import UserTable
from decimal import Decimal
from django.core.validators import MinValueValidator

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
    product_quantity = models.IntegerField()
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE,null=True,blank=True)
    sale_Price = models.DecimalField(max_digits=7, decimal_places=2)
    description = models.TextField()
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    Is_active = models.BooleanField(default=True)
    Is_deleted = models.BooleanField(default = False)
    
    def __str__(self):
        return self.name
        
    class Meta:
        db_table = 'ProductTable'


class Size(models.Model):
    size = models.CharField(max_length=50)
    
    
    def __str__(self):
        return self.size
    
    class Meta:
        db_table = 'size'


class Color(models.Model):
    color = models.CharField(max_length=50)
    
    def __str__(self):
        return self.color
    
    class Meta:
        db_table = 'color'
        
        
class VarianceTable(models.Model):
    product = models.ForeignKey("ProductTable", verbose_name="variances", on_delete=models.CASCADE,null=True,blank=True)
    size = models.ForeignKey("Size",on_delete=models.CASCADE,null=True,blank=True)
    color = models.ForeignKey("Color",on_delete=models.CASCADE,null=True,blank=True)
    Stock_Quantity = models.PositiveIntegerField()
    Price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.Product_Name}{self.color.color} - {self.size.size}"
    
    class Meta:
        db_table = 'variance_table'
    
    
class Product_Images_Table(models.Model):
    product = models.ForeignKey(ProductTable,related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/")
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    class Meta:
        db_table = 'Product_Images_Table'
        

class Cart(models.Model):
    user = models.OneToOneField("UserProfile.UserTable",
                                on_delete=models.CASCADE,
                                related_name="cart",
                                null=True,blank=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2,default = 0.00)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
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
        self.item_price = self.product_variant.Price
        self.total_price = round(self.quantity * self.item_price, 2)
        super().save(*args,**kwargs)
        self.cart.update_total()
        
        
    class Meta:
        db_table = 'Cart_item'
        #for preventing duplications
        unique_together = ['cart','product_variant']
        ordering = ['-added_at']