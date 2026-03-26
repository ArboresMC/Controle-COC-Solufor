from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0008_s3_attachment_paths'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='entryrecord',
            index=models.Index(fields=['participant', 'movement_date'], name='entry_part_date_idx'),
        ),
        migrations.AddIndex(
            model_name='entryrecord',
            index=models.Index(fields=['participant', 'status', 'movement_date'], name='entry_part_stat_dt_idx'),
        ),
        migrations.AddIndex(
            model_name='entryrecord',
            index=models.Index(fields=['product', 'movement_date'], name='entry_prod_date_idx'),
        ),
        migrations.AddIndex(
            model_name='entryrecord',
            index=models.Index(fields=['supplier', 'movement_date'], name='entry_supp_date_idx'),
        ),
        migrations.AddIndex(
            model_name='salerecord',
            index=models.Index(fields=['participant', 'movement_date'], name='sale_part_date_idx'),
        ),
        migrations.AddIndex(
            model_name='salerecord',
            index=models.Index(fields=['participant', 'status', 'movement_date'], name='sale_part_stat_dt_idx'),
        ),
        migrations.AddIndex(
            model_name='salerecord',
            index=models.Index(fields=['product', 'movement_date'], name='sale_prod_date_idx'),
        ),
        migrations.AddIndex(
            model_name='salerecord',
            index=models.Index(fields=['customer', 'movement_date'], name='sale_cust_date_idx'),
        ),
        migrations.AddIndex(
            model_name='salerecord',
            index=models.Index(fields=['supplier', 'movement_date'], name='sale_supp_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transformationrecord',
            index=models.Index(fields=['participant', 'movement_date'], name='trf_part_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transformationrecord',
            index=models.Index(fields=['source_product', 'movement_date'], name='trf_src_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transformationrecord',
            index=models.Index(fields=['target_product', 'movement_date'], name='trf_tgt_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transformationrecord',
            index=models.Index(fields=['customer', 'movement_date'], name='trf_cust_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transformationrecord',
            index=models.Index(fields=['supplier', 'movement_date'], name='trf_supp_date_idx'),
        ),
        migrations.AddIndex(
            model_name='tracelot',
            index=models.Index(fields=['participant', 'source_type', 'movement_date'], name='lot_part_src_dt_idx'),
        ),
        migrations.AddIndex(
            model_name='tracelot',
            index=models.Index(fields=['participant', 'product', 'movement_date'], name='lot_part_prod_dt_idx'),
        ),
        migrations.AddIndex(
            model_name='tracelot',
            index=models.Index(fields=['supplier', 'movement_date'], name='lot_supp_date_idx'),
        ),
        migrations.AddIndex(
            model_name='lotallocation',
            index=models.Index(fields=['participant', 'target_type'], name='alloc_part_tgt_idx'),
        ),
        migrations.AddIndex(
            model_name='lotallocation',
            index=models.Index(fields=['lot', 'target_type'], name='alloc_lot_tgt_idx'),
        ),
        migrations.AddIndex(
            model_name='lotallocation',
            index=models.Index(fields=['sale'], name='alloc_sale_idx'),
        ),
        migrations.AddIndex(
            model_name='lotallocation',
            index=models.Index(fields=['transformation'], name='alloc_trf_idx'),
        ),
    ]
