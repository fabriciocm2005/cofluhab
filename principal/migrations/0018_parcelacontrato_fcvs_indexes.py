from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0017_ocrreviewqueue_reviewqueueitem'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='parcelacontrato',
            index=models.Index(fields=['dtvenc'], name='parc_dtvenc_idx'),
        ),
        migrations.AddIndex(
            model_name='parcelacontrato',
            index=models.Index(fields=['contrato', 'dtvenc'], name='parc_cont_dtv_idx'),
        ),
    ]
