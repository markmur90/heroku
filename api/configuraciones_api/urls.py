from django.urls import path
from api.configuraciones_api import views

urlpatterns = [
    path('', views.lista_configuraciones, name='lista_configuraciones'),
    path('nueva/', views.crear_configuracion, name='crear_configuracion'),
    path('editar/<int:pk>/', views.editar_configuracion, name='editar_configuracion'),
    path('eliminar/<int:pk>/', views.eliminar_configuracion, name='eliminar_configuracion'),
]