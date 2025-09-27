from django.db import models
from accounts.models import User

# Create your models here.
class Inventory(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    quantity = models.IntegerField(default=0)
    barcode = models.CharField(max_length=50,unique=True)
    description = models.TextField(null=True, blank=True)
    supplier = models.CharField(max_length=200)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'inventory_db'

    def __str__(self):
        return f"{self.name} - {self.category} - {self.price}"