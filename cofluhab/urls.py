from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'principal/cef/p3026/visualizar/',
        RedirectView.as_view(url='/cef/p3026/visualizar/', permanent=False)
    ),
    path('', include('principal.urls')),
]
