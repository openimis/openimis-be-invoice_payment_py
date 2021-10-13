# Generated by Django 3.0.14 on 2021-10-05 09:28

import core.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_missing_roles'),
        ('invoice', '0006_auto_20210928_0939'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvoicePaymentMutation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('invoice_payment', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='mutations', to='invoice.InvoicePayment')),
                ('mutation', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='invoice_payments', to='core.MutationLog')),
            ],
            options={
                'db_table': 'invoice_InvoicePaymentMutation',
                'managed': True,
            },
            bases=(models.Model, core.models.ObjectMutation),
        ),
        migrations.CreateModel(
            name='InvoiceMutation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='mutations', to='invoice.Invoice')),
                ('mutation', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='invoices', to='core.MutationLog')),
            ],
            options={
                'db_table': 'invoice_invoiceMutation',
                'managed': True,
            },
            bases=(models.Model, core.models.ObjectMutation),
        ),
        migrations.CreateModel(
            name='InvoiceLineItemMutation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('invoice_line_items', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='mutations', to='invoice.InvoiceLineItem')),
                ('mutation', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='invoice_line_items', to='core.MutationLog')),
            ],
            options={
                'db_table': 'invoice_InvoiceLineItemsMutation',
                'managed': True,
            },
            bases=(models.Model, core.models.ObjectMutation),
        ),
    ]