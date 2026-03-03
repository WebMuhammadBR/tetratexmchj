from django.contrib import admin
from ..models.contracts import Contract

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "farmer",
        "number",
        "contract_type",
        "date",
        "planned_quantity",
        "price",
        "total_amount",
        "get_balance",
        "is_active",
    )

    list_filter = ("contract_type", "is_active", "date")
    search_fields = ("number", "farmer__name")
    ordering = ("-date",)

    def get_balance(self, obj):
        return obj.balance

    get_balance.short_description = "Шартнома баланси"
