from django.contrib import messages
from django.shortcuts import render, redirect
from store.models import Product, ReviewsRating


def home(request):
    products = Product.objects.all().filter(is_available=True).order_by('created_date')

    # Gallerie des produits
    for product in products:
        reviews = ReviewsRating.objects.filter(product_id=product.id, status=True)

    context = {
        'products': products,
        'reviews': reviews,
    }
    return render(request, 'home.html', context)



def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Logique pour ajouter l'email à ta liste de diffusion (par exemple, l'enregistrer dans la base de données)
            # Exemple :
            # NewsletterSubscriber.objects.create(email=email)

            messages.success(request, 'Merci de vous être inscrit à notre newsletter !')
            return redirect('home')  # Rediriger vers la page d'accueil ou une autre page
        else:
            messages.error(request, 'Veuillez entrer une adresse e-mail valide.')

    return render(request, 'home.html')