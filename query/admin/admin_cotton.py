from django.contrib import admin
from django import forms
from ..models.cotton import (
    GoodsReceivedDocument,
    GoodsReceivedItem,
    SelectionType,
    SortClass,
)
from ..models.contracts import Contract


# =====================================================
# 🔹 INLINE — GoodsReceivedItem
# =====================================================

class GoodsReceivedItemInline(admin.TabularInline):
    model = GoodsReceivedItem
    extra = 1

    fields = (
        "physical_weight",
        "impurity",
        "calculated_weight",
        "moisture",
        "conditional_weight",
        "selection_type",
        "sort_class",
        "price",
        "amount",
    )

    readonly_fields = (
        "calculated_weight",
        "conditional_weight",
        "price",
        "amount",
    )


# =====================================================
# 🔹 FORM — фермер танланганда шартнома фильтрланади
# =====================================================

class GoodsReceivedDocumentAdminForm(forms.ModelForm):
    class Meta:
        model = GoodsReceivedDocument
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "farmer" in self.data:
            try:
                farmer_id = int(self.data.get("farmer"))
                self.fields["contract"].queryset = Contract.objects.filter(
                    farmer_id=farmer_id
                )
            except (ValueError, TypeError):
                self.fields["contract"].queryset = Contract.objects.none()

        elif self.instance.pk:
            self.fields["contract"].queryset = Contract.objects.filter(
                farmer=self.instance.farmer
            )
        else:
            self.fields["contract"].queryset = Contract.objects.none()


# =====================================================
# 🔹 DOCUMENT ADMIN
# =====================================================

@admin.register(GoodsReceivedDocument)
class GoodsReceivedDocumentAdmin(admin.ModelAdmin):

    form = GoodsReceivedDocumentAdminForm

    list_display = (
        "number",
        "formatted_date",
        "farmer",
        "contract",
        "get_total_amount",
    )

    list_filter = ("date", "farmer")
    search_fields = ("number", "farmer__name")
    ordering = ("-date",)

    inlines = [GoodsReceivedItemInline]

    # Жами сумма
    def get_total_amount(self, obj):
        return obj.total_amount

    get_total_amount.short_description = "Жами сумма"

    # Сана формати
    def formatted_date(self, obj):
        if obj.date:
            return obj.date.strftime("%d.%m.%Y")
        return "-"

    formatted_date.short_description = "Сана"
    formatted_date.admin_order_field = "date"


# =====================================================
# 🔹 SelectionType ADMIN
# =====================================================

@admin.register(SelectionType)
class SelectionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "coefficient")
    ordering = ("type",)
    search_fields = ("name",)


# =====================================================
# 🔹 SortClass ADMIN
# =====================================================

@admin.register(SortClass)
class SortClassAdmin(admin.ModelAdmin):
    list_display = ("sort", "class_grade", "coefficient")
    ordering = ("sort", "class_grade")
