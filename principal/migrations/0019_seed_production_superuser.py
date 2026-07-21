from django.db import migrations
from django.contrib.auth.hashers import make_password


def seed_superuser(apps, schema_editor):
    User = apps.get_model("auth", "User")

    user, created = User.objects.get_or_create(
        username="cofluhab",
        defaults={
            "email": "",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )

    if not created:
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True

    user.password = make_password("cofluhab123456")
    user.save(update_fields=["password", "is_staff", "is_superuser", "is_active"])


def reverse_seed_superuser(apps, schema_editor):
    User = apps.get_model("auth", "User")
    User.objects.filter(username="cofluhab").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("principal", "0018_parcelacontrato_fcvs_indexes"),
    ]

    operations = [
        migrations.RunPython(seed_superuser, reverse_seed_superuser),
    ]
