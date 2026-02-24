from django.contrib import admin
from django.utils.html import format_html
from ..models.accounting import Ledger


@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):

    list_display = (
        "formatted_date",
        "farmer",
        "contract",
        "given_document",
        "received_document",
        "debit",
        "credit",
    )

    list_filter = (
        "date",
        "farmer",
        "contract",
    )

    search_fields = (
        "farmer__name",
        "contract__number",
    )

    ordering = ("-date",)

    # 🔥 Superuser hamma narsani o‘zgartira oladi
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        return (
            "date",
            "farmer",
            "contract",
            "given_document",
            "received_document",
            "debit",
            "credit",
        )

    # 🔥 Oddiy user linkni bosa olmaydi
    def get_list_display_links(self, request, list_display):
        if request.user.is_superuser:
            return ("formatted_date",)
        return None

    # 🔥 Qo‘shish faqat superuserga
    def has_add_permission(self, request):
        return request.user.is_superuser

    # 🔥 O‘chirish faqat superuserga
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    # 🔥 Sana format
    def formatted_date(self, obj):
        if obj.date:
            return obj.date.strftime("%d.%m.%Y")
        return "-"

    formatted_date.short_description = "Сана"
    formatted_date.admin_order_field = "date"
