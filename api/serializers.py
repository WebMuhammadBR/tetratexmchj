from rest_framework import serializers

from query.models.counterparties import Farmer
from query.models.documents import MineralWarehouseReceipt, GoodsGivenDocument, Warehouse


class FarmerSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        read_only=True
    )
    district = serializers.SerializerMethodField()

    class Meta:
        model = Farmer
        fields = (
            "id",
            "name",
            "inn",
            "maydon",
            "balance",
            "district",
        )

    def get_district(self, obj):
        massive = obj.massive
        if massive and massive.district:
            return massive.district.name
        return None


class FarmerSummarySerializer(serializers.ModelSerializer):
    quantity = serializers.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    region = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    massive = serializers.SerializerMethodField()

    class Meta:
        model = Farmer
        fields = (
            "id",
            "name",
            "inn",
            "region",
            "district",
            "massive",
            "quantity",
            "amount",
        )

    def get_region(self, obj):
        massive = obj.massive
        if massive and massive.district and massive.district.region:
            return massive.district.region.name
        return None

    def get_district(self, obj):
        massive = obj.massive
        if massive and massive.district:
            return massive.district.name
        return None

    def get_massive(self, obj):
        if obj.massive:
            return obj.massive.name
        return None


class MineralWarehouseReceiptSerializer(serializers.ModelSerializer):
    transport_type_display = serializers.CharField(source="get_transport_type_display", read_only=True)
    product = serializers.CharField(source="product.name", read_only=True)
    warehouse = serializers.CharField(source="warehouse.name", read_only=True)

    class Meta:
        model = MineralWarehouseReceipt
        fields = (
            "id",
            "date",
            "invoice_number",
            "transport_type",
            "transport_type_display",
            "transport_number",
            "bag_count",
            "product",
            "quantity",
            "price",
            "amount",
            "warehouse",
        )


class GoodsGivenDocumentSummarySerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    farmer_name = serializers.CharField(source="farmer.name", read_only=True)
    quantity = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = GoodsGivenDocument
        fields = (
            "id",
            "date",
            "number",
            "warehouse_name",
            "farmer_name",
            "quantity",
            "total_amount",
        )


class WarehouseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Warehouse
        fields = (
            "id",
            "name",
        )
