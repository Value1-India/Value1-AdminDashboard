from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('register', views.register, name='register'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('generate', views.generate, name='generate'),
    path('preview', views.preview, name='preview'),
]