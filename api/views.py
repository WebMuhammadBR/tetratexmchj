from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from query.models.bot import BotUser
from query.models.counterparties import Farmer
from query.models.documents import MineralWarehouseReceipt, GoodsGivenDocument, Warehouse
from .serializers import (
    FarmerSerializer,
    FarmerSummarySerializer,
    MineralWarehouseReceiptSerializer,
    GoodsGivenDocumentSummarySerializer,
    WarehouseSerializer,
)


class FarmerListAPIView(APIView):

    def get(self, request):
        farmers = (
            Farmer.objects
            .filter(is_active=True)
            .select_related("massive__district__region")
            .order_by(
                "massive__district__id",
                "massive__id",
                "name"
            )
        )
        serializer = FarmerSerializer(farmers, many=True)
        return Response(serializer.data)


class FarmerSummaryAPIView(ListAPIView):
    serializer_class = FarmerSummarySerializer

    def get_queryset(self):
        return (
            Farmer.objects
            .select_related("massive__district__region")
            .annotate(
                quantity=Coalesce(
                    Sum("contracts__planned_quantity"),
                    Decimal("0.00")
                ),
                amount=Coalesce(
                    Sum("contracts__total_amount"),
                    Decimal("0.00")
                ),
            )
            .order_by("massive__district__id", "massive__id")
        )


class MineralWarehouseReceiptListAPIView(ListAPIView):
    serializer_class = MineralWarehouseReceiptSerializer

    def get_queryset(self):
        return MineralWarehouseReceipt.objects.select_related("warehouse", "product").order_by("-date", "-id")


class GoodsGivenDocumentListAPIView(ListAPIView):
    serializer_class = GoodsGivenDocumentSummarySerializer

    def get_queryset(self):
        return (
            GoodsGivenDocument.objects
            .select_related("warehouse", "farmer")
            .annotate(
                quantity=Coalesce(Sum("items__quantity"), Decimal("0.00")),
            )
            .order_by("-date", "-id")
        )


class WarehouseListAPIView(ListAPIView):
    serializer_class = WarehouseSerializer

    def get_queryset(self):
        return Warehouse.objects.all().order_by("name")


class MineralWarehouseTotalsAPIView(APIView):

    def get(self, request):
        warehouse_id = request.query_params.get("warehouse_id")
        product_id = request.query_params.get("product_id")
        district_id = request.query_params.get("district_id")

        receipts = MineralWarehouseReceipt.objects.all()
        expenses = GoodsGivenDocument.objects.all()

        if warehouse_id:
            receipts = receipts.filter(warehouse_id=warehouse_id)
            expenses = expenses.filter(warehouse_id=warehouse_id)

        if product_id:
            receipts = receipts.filter(product_id=product_id)
            expenses = expenses.filter(items__product_id=product_id)
        if district_id:
            expenses = expenses.filter(farmer__massive__district_id=district_id)

        total_in = receipts.aggregate(
            value=Coalesce(Sum("quantity"), Decimal("0.00")),
            amount=Coalesce(Sum("amount"), Decimal("0.00")),
        )

        total_out = expenses.aggregate(
            value=Coalesce(Sum("items__quantity"), Decimal("0.00")),
            amount=Coalesce(Sum("items__amount"), Decimal("0.00")),
        )

        balance = total_in["value"] - total_out["value"]
        balance_amount = total_in["amount"] - total_out["amount"]

        return Response(
            {
                "total_in": total_in["value"],
                "total_out": total_out["value"],
                "balance": balance,
                "total_in_amount": total_in["amount"],
                "total_out_amount": total_out["amount"],
                "balance_amount": balance_amount,
            }
        )


class WarehouseProductsAPIView(APIView):

    def get(self, request):
        warehouse_id = request.query_params.get("warehouse_id")
        movement = request.query_params.get("movement")
        district_id = request.query_params.get("district_id")

        receipt_items = MineralWarehouseReceipt.objects.all()
        expense_items = GoodsGivenDocument.objects.all()

        if warehouse_id:
            receipt_items = receipt_items.filter(warehouse_id=warehouse_id)
            expense_items = expense_items.filter(warehouse_id=warehouse_id)
        if district_id:
            expense_items = expense_items.filter(farmer__massive__district_id=district_id)

        products_map = {}

        if movement in (None, "", "all", "in"):
            for row in (
                receipt_items
                .values("product_id", "product__name")
                .annotate(total_in=Coalesce(Sum("quantity"), Decimal("0.00")))
            ):
                product_id = row["product_id"]
                if not product_id:
                    continue

                product = products_map.setdefault(
                    product_id,
                    {
                        "product_id": product_id,
                        "product_name": row["product__name"] or "-",
                        "total_in": Decimal("0.00"),
                        "total_out": Decimal("0.00"),
                    }
                )
                product["total_in"] = row["total_in"]

        if movement in (None, "", "all", "out"):
            for row in (
                expense_items
                .values("items__product_id", "items__product__name")
                .annotate(total_out=Coalesce(Sum("items__quantity"), Decimal("0.00")))
            ):
                product_id = row["items__product_id"]
                if not product_id:
                    continue

                product = products_map.setdefault(
                    product_id,
                    {
                        "product_id": product_id,
                        "product_name": row["items__product__name"] or "-",
                        "total_in": Decimal("0.00"),
                        "total_out": Decimal("0.00"),
                    }
                )
                product["total_out"] = row["total_out"]

        products = sorted(products_map.values(), key=lambda item: item["product_name"])

        for item in products:
            item["balance"] = item["total_in"] - item["total_out"]

        return Response(products)


class WarehouseExpenseDistrictsAPIView(APIView):

    def get(self, request):
        warehouse_id = request.query_params.get("warehouse_id")

        expense_items = GoodsGivenDocument.objects.select_related("farmer__massive__district")
        if warehouse_id:
            expense_items = expense_items.filter(warehouse_id=warehouse_id)

        districts = {}
        for item in expense_items:
            farmer = item.farmer
            if not farmer or not farmer.massive or not farmer.massive.district:
                continue

            district = farmer.massive.district
            districts[district.id] = district.name

        result = [
            {"district_id": district_id, "district_name": district_name}
            for district_id, district_name in sorted(districts.items(), key=lambda row: row[1])
        ]

        return Response(result)


class WarehouseMovementsAPIView(APIView):

    def get(self, request):
        warehouse_id = request.query_params.get("warehouse_id")
        product_id = request.query_params.get("product_id")
        district_id = request.query_params.get("district_id")
        movement = request.query_params.get("movement")

        if movement not in {"in", "out"}:
            return Response([])

        if movement == "in":
            receipts = MineralWarehouseReceipt.objects.select_related("warehouse", "product")

            if warehouse_id:
                receipts = receipts.filter(warehouse_id=warehouse_id)
            if product_id:
                receipts = receipts.filter(product_id=product_id)

            return Response(
                [
                    {
                        "id": item.id,
                        "date": item.date,
                        "warehouse_name": item.warehouse.name if item.warehouse else None,
                        "product_id": item.product_id,
                        "product_name": item.product.name if item.product else None,
                        "invoice_number": item.invoice_number,
                        "bag_count": item.bag_count,
                        "quantity": item.quantity,
                    }
                    for item in receipts.order_by("-date", "-id")
                ]
            )

        expense_items = (
            GoodsGivenDocument.objects
            .select_related("warehouse", "farmer")
            .prefetch_related("items__product")
        )

        if warehouse_id:
            expense_items = expense_items.filter(warehouse_id=warehouse_id)
        if product_id:
            expense_items = expense_items.filter(items__product_id=product_id)
        if district_id:
            expense_items = expense_items.filter(farmer__massive__district_id=district_id)

        result = []
        rows = (
            expense_items
            .values("farmer_id", "farmer__name", "farmer__maydon")
            .annotate(quantity=Coalesce(Sum("items__quantity"), Decimal("0.00")))
            .order_by("farmer__name")
        )

        for index, row in enumerate(rows, start=1):
            maydon = row.get("farmer__maydon") or Decimal("0.00")
            quantity = row.get("quantity") or Decimal("0.00")
            quantity_per_area = Decimal("0.00")
            if maydon > 0:
                quantity_per_area = quantity / maydon

            result.append(
                {
                    "id": index,
                    "date": None,
                    "warehouse_name": None,
                    "number": "-",
                    "farmer_name": row.get("farmer__name") or "-",
                    "product_id": None,
                    "product_name": "-",
                    "quantity": quantity,
                    "maydon": maydon,
                    "quantity_per_area": quantity_per_area,
                }
            )

        return Response(result)


class BotUserCheckAPIView(APIView):

    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        full_name = request.data.get("full_name")

        user, created = BotUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "full_name": full_name,
                "is_active": False,
            }
        )

        return Response({
            "allowed": user.is_active,
            "created": created
        })
