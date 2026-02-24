from django.contrib import admin
from ..models.counterparties import Farmer, BankAccount


class BankAccountInline(admin.TabularInline):
    model = BankAccount
    extra = 1
    fields = ("bank_name", "account_number", "mfo", "is_main")


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "inn",
        "maydon",
        "massive",
        "is_active",
        "get_balance",
    )

    list_filter = ("is_active", "massive")
    search_fields = ("name", "inn")
    ordering = ("name",)
    inlines = [BankAccountInline]

    def get_balance(self, obj):
        return obj.balance

    get_balance.short_description = "Баланс"


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "farmer", "bank_name", "account_number", "mfo", "is_main")
    list_filter = ("is_main", "bank_name")
    search_fields = ("account_number", "farmer__name")
