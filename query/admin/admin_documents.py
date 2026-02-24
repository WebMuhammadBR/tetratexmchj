from django.contrib import admin
from django import forms
from ..models.documents import GoodsGivenDocument, GoodsGivenItem, MineralWarehouseReceipt, Warehouse
from ..models.contracts import Contract


# =====================================================
# 🔹 INLINE — GoodsGivenItem
# =====================================================

class GoodsGivenItemInline(admin.TabularInline):
    model = GoodsGivenItem
    extra = 1

    fields = (
        "product",
        "quantity",
        "price",
        "vat_rate",
        "amount",
        "vat_amount",
        "total_with_vat",
    )

    readonly_fields = (
        "amount",
        "vat_amount",
        "total_with_vat",
    )


# =====================================================
# 🔹 FORM — фермер танланганда шартнома фильтрланади
# =====================================================

class GoodsGivenDocumentAdminForm(forms.ModelForm):
    class Meta:
        model = GoodsGivenDocument
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # POST пайтида
        if "farmer" in self.data:
            try:
                farmer_id = int(self.data.get("farmer"))
                self.fields["contract"].queryset = Contract.objects.filter(
                    farmer_id=farmer_id
                )
            except (ValueError, TypeError):
                self.fields["contract"].queryset = Contract.objects.none()

        # Edit ҳолати
        elif self.instance.pk:
            self.fields["contract"].queryset = Contract.objects.filter(
                farmer=self.instance.farmer
            )
        else:
            self.fields["contract"].queryset = Contract.objects.none()




@admin.register(MineralWarehouseReceipt)
class MineralWarehouseReceiptAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "invoice_number",
        "transport_type",
        "transport_number",
        "bag_count",
        "product",
        "quantity",
        "price",
        "amount",
        "warehouse",
    )
    list_filter = ("date", "warehouse", "transport_type", "product")
    search_fields = ("invoice_number", "transport_number", "warehouse__name", "product__name")
    readonly_fields = ("amount",)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)

# =====================================================
# 🔹 ADMIN — GoodsGivenDocument
# =====================================================

@admin.register(GoodsGivenDocument)
class GoodsGivenDocumentAdmin(admin.ModelAdmin):

    form = GoodsGivenDocumentAdminForm

    list_display = (
        "number",
        "formatted_date",
        "farmer",
        "contract",
        "warehouse",
        "get_total_amount",
    )

    list_filter = ("date", "farmer", "warehouse")
    search_fields = ("number", "farmer__name")
    ordering = ("-date",)

    inlines = [GoodsGivenItemInline]

    # 🔹 Жами сумма
    def get_total_amount(self, obj):
        return obj.total_amount

    get_total_amount.short_description = "Жами сумма"

    # 🔹 Санани chiroyli format
    def formatted_date(self, obj):
        if obj.date:
            return obj.date.strftime("%d.%m.%Y")
        return "-"

    formatted_date.short_description = "Сана"
    formatted_date.admin_order_field = "date"
