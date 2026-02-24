from django.contrib import admin
from ..models.reference import Unit, Product, Region, District, Massive


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "short_name")
    search_fields = ("name", "short_name")
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "unit", "is_active")
    list_filter = ("is_active", "unit")
    search_fields = ("name",)
    list_editable = ("is_active",)
    ordering = ("name",)


class DistrictInline(admin.TabularInline):
    model = District
    extra = 1


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    inlines = [DistrictInline]
    ordering = ("name",)


class MassiveInline(admin.TabularInline):
    model = Massive
    extra = 1


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "region")
    list_filter = ("region",)
    search_fields = ("name",)
    inlines = [MassiveInline]
    ordering = ("name",)


@admin.register(Massive)
class MassiveAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "district")
    list_filter = ("district",)
    search_fields = ("name",)
    ordering = ("name",)
