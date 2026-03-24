from django.db import migrations, models
import transactions.models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0007_transformationrecord_output_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entryrecord',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to=transactions.models.entry_attachment_path),
        ),
        migrations.AlterField(
            model_name='salerecord',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to=transactions.models.sale_attachment_path),
        ),
        migrations.AlterField(
            model_name='transformationrecord',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to=transactions.models.transformation_attachment_path),
        ),
    ]
