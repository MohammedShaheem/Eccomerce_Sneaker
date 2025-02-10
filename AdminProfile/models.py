from django.db import models

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
        
    