# Generated by Django 3.0.14 on 2021-09-13 12:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalinvoicepayment',
            name='date_valid_from',
        ),
        migrations.RemoveField(
            model_name='historicalinvoicepayment',
            name='date_valid_to',
        ),
        migrations.RemoveField(
            model_name='historicalinvoicepayment',
            name='replacement_uuid',
        ),
        migrations.RemoveField(
            model_name='invoicepayment',
            name='date_valid_from',
        ),
        migrations.RemoveField(
            model_name='invoicepayment',
            name='date_valid_to',
        ),
        migrations.RemoveField(
            model_name='invoicepayment',
            name='replacement_uuid',
        ),
    ]