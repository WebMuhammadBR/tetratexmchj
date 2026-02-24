from django.db import models


class BotUser(models.Model):
    telegram_id = models.BigIntegerField("Telegram ID", unique=True)
    full_name = models.CharField("Ф.И.О", max_length=255)
    is_active = models.BooleanField("Фаол", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bot фойдаланувчи"
        verbose_name_plural = "Bot фойдаланувчилар"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.telegram_id})"
