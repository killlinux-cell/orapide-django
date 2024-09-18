import datetime
import json

from django.contrib import messages
import requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from Rapidestore import settings
from carts.models import CartItem
from orders.forms import OrderForm
from orders.models import Order, Payment, OrderProduct
import json

from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string, get_template
from xhtml2pdf import pisa
from django.shortcuts import render, redirect
from .services import PayDunyaAPI


#sans api de paiement
def process_payment(request):

    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Insertion des détails des transactions pour insérer dans le modèle de paiement
    payment = Payment(
        user=request.user,
        payment_id=body['transID'],  # Utilisation du transID généré côté client
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status'],
        )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    # Déplacer les items du panier dans Order
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()

        # Réduire la quantité du produit restant
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # vider le panier
    CartItem.objects.filter(user=request.user).delete()

    # Transferer les données de l'achats au mail du clients
    mail_subject = 'Merci pour votre commande votre commande'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Envoyer le numero de commande et transaction id to send data methon via JSONResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)




def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    #Insertion sur les details des transactions pour inserer dans le model de paiement
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    #Deplacer le cart items dans Order
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()

        # Réduire la quantité du produit restant
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()
    # vider le panier
    CartItem.objects.filter(user=request.user).delete()
    # Transferer les données de l'achats au mail du clients
    mail_subject = 'Merci pour votre commande votre commande'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Envoyer le numero de commande et transaction id to send data methon via JSONResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)


def place_order(request, total=0, quantity=0):
    current_user = request.user




    # si le panier est vide je redirige vers le home
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    livraison = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    livraison = int((2 * total) / 100)
    grand_total = total + livraison


    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            #sauvegarder toutes les données dans la table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.livraison = livraison
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%d%m%Y")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()


            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'livraison': livraison,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
        else:
            messages.error(request, 'PROBLEME')
            return redirect('checkout')

    else:
        return redirect('checkout')



def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')





import requests
from django.http import JsonResponse

def initiate_payment(request):
    # Headers pour l'API PayDunya
    headers = {
        "Content-Type": "application/json",
        "PAYDUNYA-MASTER-KEY": "STcNmJm6-m2Cw-sTbj-74my-l4e7YfJfqZ7B",
        "PAYDUNYA-PRIVATE-KEY": "test_private_1YuB6ljZFYnGPu5JeoIoitK9b7F",
        "PAYDUNYA-TOKEN": "Y1Xp46l5WnyQb3Qgcjao",
    }

    # Corps de la requête
    data = {
        "invoice": {
            "total_amount": 5000,
            "description": "Chaussure VANS dernier modèle"
        },
        "store": {
            "name": "Magasin le Choco"
        }
    }

    # Envoi de la requête POST à l'API PayDunya
    response = requests.post(
        "https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create",
        json=data,
        headers=headers
    )

    # Retourner la réponse JSON
    return JsonResponse(response.json())
