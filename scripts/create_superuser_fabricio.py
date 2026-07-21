import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = 'Fabricio'
password = '123456'
email = 'fabricio@example.com'

u = User.objects.filter(username=username).first()
if u:
    u.set_password(password)
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print('updated superuser Fabricio')
else:
    User.objects.create_superuser(username, email, password)
    print('created superuser Fabricio')
