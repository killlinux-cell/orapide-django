from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from orders.models import Order, OrderProduct
from carts.models import Cart, CartItem
from carts.views import _cart_id
from orders.models import Order
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
import requests


# Create your views here.
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            username = email.split("@")[0]

            user = Account.objects.create_user(first_name=first_name,last_name=last_name,email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            # Activation de l'utilisateur
            current_site = get_current_site(request)
            mail_subject = 'Veuillez activer votre compte'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            #/accounts/login/?command=verificaton&email='+email' messages.success(request, 'Merci! pour votre inscription. Nous vous avons envoyé un e-mail de vérification à votre adresse e-mail. Veuillez le vérifier.')
            return redirect(f"{reverse('login')}?command=verification&email={email}")
    else:
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    # Recevoir la variation des produit par ID
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # Recevoir le contenu du panier par le biais de l'utilisateur pour acceder aux variations

                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    #product_variation = [1,2,3,4,6]
                    #ex_var_list = [4,6,3,5]

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()

            except:
                pass
            auth.login(request, user)
            messages.success(request, 'vous êtes connecté')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                # next=/cart/checkout
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('dashboard')
        else:
            messages.error(request, 'Identifiants de connexion invalides')
            return redirect('login')
    return render(request, 'accounts/login.html')

@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'vous êtes déconnecté')
    return redirect('login')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None


    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Félicitation! Votre compte est activé')
        return redirect('login')
    else:
        messages.error(request, "Le lien d'activation est invalide")
        return redirect('register')

@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()

    userprofile = UserProfile.objects.get(user_id=request.user.id)
    context = {
        'orders_count': orders_count,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/dashboard.html', context)


def forgotPassword(request):
        if request.method == 'POST':
            email = request.POST['email']
            if Account.objects.filter(email=email).exists():
                user = Account.objects.get(email__exact=email)

                # Réinitialiser le mot de pase
                current_site = get_current_site(request)
                mail_subject = 'Réinitialisation du mot de passe'
                message = render_to_string('accounts/reset_password_email.html', {
                    'user': user,
                    'domain': current_site,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                })
                to_email = email
                send_email = EmailMessage(mail_subject, message, to=[to_email])
                send_email.send()

                messages.success(request, 'Le lien de réinitialisation a été envoyé dans votre mail')
                return redirect('login')

            else:
                messages.error(request, "Le compte n'existe pas")
                return redirect('forgotPassword')
        return render(request, 'accounts/forgotPassword.html')



def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Veuillez réinitialiser votre mot de passe')
        return redirect('resetPassword')
    else:
        messages.error(request, 'Ce lien a expiré')
        return redirect('login')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)

            user.set_password(password)
            user.save()
            messages.success(request, 'Le mot de passe a été changé')
            return redirect('login')

        else:
            messages.error(request, "Mot de passe n'est pas identique!")
            return redirect('resetPassword')

    else:
        return render(request, 'accounts/resetPassword.html')


@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/my_orders.html', context)






@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Votre profil a été mis à jour')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    # Gestion de l'image de profil par défaut
    if userprofile.profile_picture:
        profile_url = userprofile.profile_picture.url
    else:
        profile_url = 'images/user.png'  # Chemin vers votre image par défaut

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
        'profile_url': profile_url,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Votre mot de passe a été modifier')
                return redirect('change_password')
            else:
                messages.error(request, "Vérifie l'actuel mot de passe")
                return redirect('change_password')
        else:
            messages.error(request, "Le mot de passe ne correspond pas")
            return redirect('change_password')
    return render(request, 'accounts/change_password.html')


@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity
    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'accounts/order_detail.html', context)