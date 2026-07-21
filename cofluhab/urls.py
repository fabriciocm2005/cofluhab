from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
    path(
        'principal/cef/p3026/visualizar/',
        RedirectView.as_view(url='/cef/p3026/visualizar/', permanent=False)
    ),
    path('', include('principal.urls')),
]
