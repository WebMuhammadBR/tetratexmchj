from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("query", "0012_remove_farmer_phone_farmer_maydon"),
    ]

    operations = [
        migrations.CreateModel(
            name="BotUserActivity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "action_type",
                    models.CharField(
                        choices=[("message", "Хабар"), ("callback", "Тугма"), ("system", "Тизим")],
                        max_length=20,
                        verbose_name="Ҳаракат тури",
                    ),
                ),
                ("action_name", models.CharField(max_length=100, verbose_name="Ҳаракат номи")),
                ("action_payload", models.TextField(blank=True, verbose_name="Маълумот")),
                ("is_allowed", models.BooleanField(default=True, verbose_name="Рухсат берилган")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Вақти")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="activities",
                        to="query.botuser",
                        verbose_name="Фойдаланувчи",
                    ),
                ),
            ],
            options={
                "verbose_name": "Bot фаоллик",
                "verbose_name_plural": "Bot фаолликлари",
                "ordering": ["-created_at"],
            },
        ),
    ]
