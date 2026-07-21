# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0005_contrato_parcelacontrato'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrato',
            name='cod_imovel',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='contrato',
            name='data_contrato',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contrato',
            name='data_primeiro_venc',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contrato',
            name='sa',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='contrato',
            name='tx_juros',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='contrato',
            name='prazo',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contrato',
            name='cat_prof',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='contrato',
            name='pr',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
