# Generated by Django 5.0.6 on 2024-06-27 04:47

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_rename_itemno_inspectionacceptancereport_item_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='inspectionacceptancereport',
            old_name='DateCreated',
            new_name='created_at',
        ),
        migrations.RenameField(
            model_name='purchaseorder',
            old_name='DateCreated',
            new_name='created_at',
        ),
        migrations.RenameField(
            model_name='purchaserequest',
            old_name='DateCreated',
            new_name='created_at',
        ),
        migrations.RenameField(
            model_name='requisitionissueslip',
            old_name='DateCreated',
            new_name='created_at',
        ),
        migrations.RenameField(
            model_name='supplier',
            old_name='DateCreated',
            new_name='created_at',
        ),
        migrations.RemoveField(
            model_name='item',
            name='TotalCost',
        ),
        migrations.AddField(
            model_name='item',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
    ]
