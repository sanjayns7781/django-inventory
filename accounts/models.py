from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager

# Create your models here.
class Role(models.Model):
    ROLE_CHOICES = [
        ("ADMIN","ADMIN"),
        ("MANAGER","MANAGER"),
        ("USER","USER"),
    ]
    role_name = models.CharField(max_length=120,choices=ROLE_CHOICES)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'role_db'

    def __str__(self):
        return self.role_name
    
    
class UserManager(BaseUserManager):
    def create_user(self,username,email,password=None,**extra_fields):
        if not email:
            raise ValueError("Email field must be not none")
        email = self.normalize_email(email)
        user = self.model(username=username,email=email,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields['role'] = Role.objects.get(name="ADMIN")
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    username = models.CharField(max_length=150,unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.ForeignKey(Role,on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True,blank=True)

    objects = UserManager()
    
    class Meta:
        db_table = 'user_db'

    def __str__(self):
        return f"{self.username}----{self.email}-----{self.role}"
