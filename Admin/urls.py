from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('generate', views.generate, name='generate'),
    path('preview', views.preview, name='preview'),
    path('webhook', views.webhook_view, name='webhook_view'),
    path('cleanup', views.cleanup, name='cleanup'),
    path('test', views.test, name='test'),
]