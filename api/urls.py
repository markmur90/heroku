from django.urls import path, include
from django.contrib import admin
from api.gpt4.views import oauth2_authorize, oauth2_callback
from api.views import (
    DashboardView, HomeView, AuthIndexView, CoreIndexView, AccountsIndexView, SCTIndexView,
    TransactionsIndexView, TransfersIndexView, CollectionIndexView, cambiar_entorno, login_view, logout_view, mostrar_readme, ReadmeView, AuthorizeView, CallbackView, signup_view, dashboard_view
)

urlpatterns = [
    # Asegúrate de que solo haya un namespace 'admin'
    path('', HomeView.as_view(), name='home'),
    # path('login/', LoginView.as_view(), name='login'),
    # path('logout/', LogoutView.as_view(), name='logout'),
    # path('app/api/auth/index.html', AuthIndexView.as_view(), name='auth_index'),
    path('app/core/index.html', CoreIndexView.as_view(), name='core_index'),
    # path('app/accounts/index.html', AccountsIndexView.as_view(), name='accounts_index'),
    # path('app/transactions/index.html', TransactionsIndexView.as_view(), name='transactions_index'),
    path('app/transfers/index.html', TransfersIndexView.as_view(), name='transfers_index'),
    # path('app/collection/index.html', CollectionIndexView.as_view(), name='collection_index'),
    # path('app/sct/index.html', SCTIndexView.as_view(), name='sct_index'),

    # path("readme/", ReadmeView.as_view(), name="readme_deploy"),
    path("readme/", mostrar_readme, name="readme_deploy"),

    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    # path('oauth2/callback/', CallbackView.as_view(), name='oauth2_callback'),
    # path('oauth2/authorize/', AuthorizeView.as_view(), name='oauth2_authorize'),
    
    path('oauth2/authorize/', oauth2_authorize, name='oauth2_authorize'),
    path('oauth2/callback/', oauth2_callback, name='oauth2_callback'),
    
    
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('signup/', signup_view, name='signup'),
    # path('dashboard/', dashboard_view, name='dashboard'),
    
    path('configuraciones/', include('api.configuraciones_api.urls')),
    path('cambiar-entorno/<str:entorno>/', cambiar_entorno, name='cambiar_entorno'),

]