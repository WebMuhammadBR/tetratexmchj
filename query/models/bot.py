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


class BotUserActivity(models.Model):
    ACTION_MESSAGE = "message"
    ACTION_CALLBACK = "callback"
    ACTION_SYSTEM = "system"

    ACTION_CHOICES = (
        (ACTION_MESSAGE, "Хабар"),
        (ACTION_CALLBACK, "Тугма"),
        (ACTION_SYSTEM, "Тизим"),
    )

    user = models.ForeignKey(
        BotUser,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name="Фойдаланувчи",
    )
    action_type = models.CharField("Ҳаракат тури", max_length=20, choices=ACTION_CHOICES)
    action_name = models.CharField("Ҳаракат номи", max_length=100)
    action_payload = models.TextField("Маълумот", blank=True)
    is_allowed = models.BooleanField("Рухсат берилган", default=True)
    created_at = models.DateTimeField("Вақти", auto_now_add=True)

    class Meta:
        verbose_name = "Bot фаоллик"
        verbose_name_plural = "Bot фаолликлари"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} - {self.action_name} ({self.created_at})"
