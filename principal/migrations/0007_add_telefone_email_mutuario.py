# Generated manually on 2025-11-26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0006_add_contrato_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='mutuario',
            name='telefone',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='mutuario',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=100),
        ),
    ]
