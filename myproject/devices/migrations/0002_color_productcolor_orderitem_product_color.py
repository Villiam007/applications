# Generated by Django 5.2 on 2025-04-19 10:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Color',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('hex_code', models.CharField(help_text='Color hex code (e.g. #FF5733)', max_length=7)),
            ],
        ),
        migrations.CreateModel(
            name='ProductColor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, help_text='Image showing the product in this color', null=True, upload_to='product_color_images/')),
                ('stock', models.PositiveIntegerField(default=0)),
                ('is_default', models.BooleanField(default=False)),
                ('color', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='devices.color')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='colors', to='devices.product')),
            ],
            options={
                'unique_together': {('product', 'color')},
            },
        ),
        migrations.AddField(
            model_name='orderitem',
            name='product_color',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='devices.productcolor'),
        ),
    ]
