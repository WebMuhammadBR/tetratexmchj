from django.contrib import admin
from ..models.bot import BotUser


@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "telegram_id", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("full_name", "telegram_id")
    ordering = ("-created_at",)
