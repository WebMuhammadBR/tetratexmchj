from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("query", "0013_botuseractivity"),
    ]

    operations = [
        migrations.AddField(
            model_name="contract",
            name="contract_type",
            field=models.CharField(
                choices=[
                    ("futures", "Фючерс"),
                    ("forward", "Форвард"),
                    ("storage", "Сақлаш"),
                ],
                default="futures",
                max_length=20,
                verbose_name="Шартнома тури",
            ),
        ),
    ]
