from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseServerError
from django.contrib.auth.models import User
from django.db import IntegrityError
import logging
from api.authentication.serializers import JWTTokenSerializer
from api.gpt4.models import Creditor, Transfer

logger = logging.getLogger(__name__)


class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

@method_decorator(login_required, name='dispatch')
class AuthIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/auth/index.html')

@method_decorator(login_required, name='dispatch')
class CoreIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/core/index.html')

@method_decorator(login_required, name='dispatch')
class AccountsIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/accounts/index.html')

@method_decorator(login_required, name='dispatch')
class TransactionsIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/transactions/index.html')

@method_decorator(login_required, name='dispatch')
class TransfersIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/transfers/index.html')

@method_decorator(login_required, name='dispatch')
class CollectionIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/collection/index.html')

@method_decorator(login_required, name='dispatch')
class SCTIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/sct/index.html')

@method_decorator(login_required, name='dispatch')
class ReadmeView(View):
    def get(self, request):
        return render(request, 'readme.html')


# ============================================================================

@method_decorator(login_required, name='dispatch')
class AuthorizeView(View):
    def get(self, request):
        return render(request, 'api/GPT4/oauth2_authorize.html')

@method_decorator(login_required, name='dispatch')
class CallbackView(View):
    def get(self, request):
        return render(request, 'api/GPT4/oauth2_callback.html')

import markdown
from pathlib import Path
from django.shortcuts import render

def mostrar_readme(request):
    readme_path = Path(__file__).resolve().parent.parent / "README.md"
    contenido_md = readme_path.read_text(encoding="utf-8")
    contenido_html = markdown.markdown(
        contenido_md,
        extensions=["fenced_code", "tables", "toc"]
    )
    return render(request, "readme.html", {"contenido_html": contenido_html})

# ============================================================================

def cambiar_entorno(request, entorno):
    if entorno in ['local', 'production']:
        request.session['entorno_actual'] = entorno
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def dashboard_view(request):
    transfers = Transfer.objects.all()
    return render(request, 'dashboard.html', {
        'transfers': transfers
    })

@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        creditors = Creditor.objects.all()
        transfers = Transfer.objects.all()
        return render(request, 'dashboard.html', {
            'creditors': creditors,
            'transfers': transfers
        })

def logout_view(request):
    username = request.user.username if request.user.is_authenticated else "desconocido"
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    logger.info(f"Usuario '{username}' cerró sesión.")
    return redirect('login')

@csrf_protect
def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        super_password = request.POST.get("super_password")

        if not username or not password1 or not password2 or not super_password:
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, "signup.html", status=400)

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, "signup.html", status=400)

        try:
            superuser = User.objects.filter(is_superuser=True).first()
            if not superuser or not superuser.check_password(super_password):
                messages.error(request, "Contraseña de administrador incorrecta.")
                return render(request, "signup.html", status=403)

            user = User.objects.create_user(username=username, password=password1)
            login(request, user)
            messages.success(request, f"Bienvenido, {user.username}")
            logger.info(f"Nuevo usuario registrado: {user.username}")
            return redirect('dashboard')

        except IntegrityError:
            messages.error(request, "El nombre de usuario ya está en uso.")
            return render(request, "signup.html", status=409)

        except Exception as e:
            logger.error(f"Error durante registro: {str(e)}", exc_info=True)
            messages.error(request, "Se produjo un error inesperado.")
            return render(request, "signup.html", status=500)

    return render(request, "signup.html")

@csrf_protect
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenido, {user.username}")
                return redirect('dashboard')

            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, "login.html", status=401)

        except Exception as e:
            logger.error(f"Error inesperado durante login: {str(e)}", exc_info=True)
            return HttpResponseServerError("Se ha producido un error inesperado. Intenta nuevamente.")

    return render(request, "login.html")


