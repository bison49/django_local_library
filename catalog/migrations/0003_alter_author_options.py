# Generated by Django 4.1.2 on 2022-10-10 08:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_language_alter_book_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='author',
            options={'ordering': ['last_name', 'first_name'], 'permissions': (('can_change_author', 'can modified author'),)},
        ),
    ]
