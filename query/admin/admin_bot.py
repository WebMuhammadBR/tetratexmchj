from django.contrib import admin

from ..models.bot import BotUser, BotUserActivity


@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "telegram_id", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("full_name", "telegram_id")
    ordering = ("-created_at",)


@admin.register(BotUserActivity)
class BotUserActivityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "action_type",
        "action_name",
        "is_allowed",
        "created_at",
    )
    list_filter = ("action_type", "is_allowed", "created_at")
    search_fields = ("user__full_name", "user__telegram_id", "action_name", "action_payload")
    ordering = ("-created_at",)
