from django.db import models
from django.conf import settings
import uuid

# It's best practice to reference the custom user model this way.
USER_MODEL = settings.AUTH_USER_MODEL

class Product(models.Model):
    """
    Represents a school supply item available for order or reservation.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in PHP")
    stock_quantity = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=100, blank=True)
    image_url = models.URLField(max_length=1024, blank=True, null=True)
    is_available = models.BooleanField(default=True, help_text="Is the product available for students to see and order?")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    """
    Represents both a student's order for an in-stock item and a reservation
    for an out-of-stock item (backorder).
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        COMPLETED = 'completed', 'Completed'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    class OrderType(models.TextChoices):
        ORDER = 'order', 'Order'
        RESERVATION = 'reservation', 'Reservation'

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='orders')
    
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    order_type = models.CharField(max_length=20, choices=OrderType.choices, default=OrderType.ORDER)
    payment_method = models.CharField(max_length=50, default='Cash')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order_type.title()} #{self.id} by {self.user.email}"

class ActivityLog(models.Model):
    """
    Logs significant actions performed by admin users for auditing.
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    details = models.JSONField(default=dict, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"