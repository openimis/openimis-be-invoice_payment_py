# Generated by Django 3.0.14 on 2021-10-13 08:05

import core.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_missing_roles'),
        ('invoice', '0007_invoicelineitemmutation_invoicemutation_invoicepaymentmutation'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvoiceEventMutation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('invoice_event', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='mutations', to='invoice.InvoiceEvent')),
                ('mutation', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='event_messages', to='core.MutationLog')),
            ],
            options={
                'db_table': 'invoice_InvoiceEventMutation',
                'managed': True,
            },
            bases=(models.Model, core.models.ObjectMutation),
        ),
    ]
