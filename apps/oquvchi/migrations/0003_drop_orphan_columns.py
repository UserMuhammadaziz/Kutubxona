# Javob: eski modeldan qolgan, kodda ishlatilmaydigan ustunlarni olib tashlash
# (holat, sinf, sinfi NOT NULL + default'siz bo'lgani o'quvchi yaratishni buzardi)
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oquvchi', '0002_alter_oquvchi_telefon'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE oquvchi_oquvchi DROP COLUMN IF EXISTS holat, DROP COLUMN IF EXISTS sinf, DROP COLUMN IF EXISTS sinfi;',
            reverse_sql='''ALTER TABLE oquvchi_oquvchi ADD COLUMN IF NOT EXISTS holat varchar(50) NULL,
                           ADD COLUMN IF NOT EXISTS sinf varchar(200) NULL,
                           ADD COLUMN IF NOT EXISTS sinfi varchar(200) NULL;''',
        ),
    ]