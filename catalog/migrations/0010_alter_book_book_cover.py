# Generated by Django 4.1.2 on 2022-10-17 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0009_alter_book_book_cover'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='book_cover',
            field=models.ImageField(blank=True, null=True, upload_to='images/'),
        ),
    ]
