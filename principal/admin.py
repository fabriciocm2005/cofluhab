from django.contrib import admin
# principal/admin.py

from django.contrib import admin
from .models import Cliente 

# Registra o Model Cliente
admin.site.register(Cliente)
# Register your models here.
