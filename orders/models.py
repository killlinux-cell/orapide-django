from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Account
from store.models import Product, Variation


# Create your models here.
class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id


class Order(models.Model):
    STATUS = (
        ('Nouveau', 'Nouveau'),
        ('Accepté', 'Accepté'),
        ('Achevé', 'Achevé'),
        ('Annulé', 'Annulé'),
    )

    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    order_note = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50)
    order_total = models.FloatField()
    livraison = models.FloatField()
    status = models.CharField(max_length=10, choices=STATUS, default='Nouveau')
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'

    def full_name(self):
        return f'{self.first_name} {self.last_name}'


    def __str__(self):
        return self.first_name

@receiver(post_save, sender=Order)
def notify_admin_on_new_order(sender, instance, created, **kwargs):
    if created:
        # Envoie un email à l'administrateur
        send_mail(
            'Nouvelle commande créée',
            f'Une nouvelle commande a été passée par {instance.user.email}.',
            'orapide.israel@outlook.com',  # Remplace par ton adresse email
            ['anakoisrael352@gmail.com'],  # Remplace par l'email de l'administrateur
            fail_silently=False,
        )


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.product_name


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email