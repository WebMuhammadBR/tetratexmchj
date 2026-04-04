from decimal import Decimal

from django.db.models import Sum, Min, Max, Count, Q
from django.db.models.functions import Coalesce
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from query.models.bot import BotUser, BotUserActivity
from query.models.counterparties import Farmer
from query.models.documents import MineralWarehouseReceipt, GoodsGivenDocument, GoodsGivenItem, Warehouse
from query.models.reference import Product
from .serializers import (
    FarmerSerializer,
    FarmerSummarySerializer,
    MineralWarehouseReceiptSerializer,
    GoodsGivenDocumentSummarySerializer,
    WarehouseSerializer,
)


class FarmerListAPIView(APIView):

    def get(self, request):
        product_names = list(
            Product.objects
            .filter(is_active=True)
            .order_by("name")
            .values_list("name", flat=True)
        )

        farmers = (
            Farmer.objects
            .filter(is_active=True)
            .select_related("massive__district__region")
            .prefetch_related("contracts")
            .annotate(
                futures_quantity=Coalesce(
                    Sum("contracts__planned_quantity", filter=Q(contracts__contract_type="futures")),
                    Decimal("0.00"),
                ),
                futures_amount=Coalesce(
                    Sum("contracts__total_amount", filter=Q(contracts__contract_type="futures")),
                    Decimal("0.00"),
                ),
            )
            .order_by(
                "massive__district__id",
                "massive__id",
                "name"
            )
        )

        serializer = FarmerSerializer(farmers, many=True)
        farmer_rows = serializer.data

        product_totals_by_farmer: dict[int, dict[str, Decimal]] = {}
        totals_rows = (
            GoodsGivenItem.objects
            .filter(document__farmer_id__in=[farmer.id for farmer in farmers])
            .values("document__farmer_id", "product__name")
            .annotate(total_amount=Coalesce(Sum("total_with_vat"), Decimal("0.00")))
        )

        for row in totals_rows:
            farmer_id = row.get("document__farmer_id")
            product_name = row.get("product__name") or "-"
            total_amount = row.get("total_amount") or Decimal("0.00")
            farmer_totals = product_totals_by_farmer.setdefault(farmer_id, {})
            farmer_totals[product_name] = total_amount

        for farmer_row in farmer_rows:
            farmer_id = farmer_row.get("id")
            product_totals = product_totals_by_farmer.get(farmer_id, {})
            farmer_row["product_totals"] = {
                product_name: product_totals.get(product_name, Decimal("0.00"))
                for product_name in product_names
            }
            farmer_row["farmer_total_amount"] = sum(product_totals.values(), Decimal("0.00"))

        return Response(farmer_rows)


class FarmerSummaryAPIView(ListAPIView):
    serializer_class = FarmerSummarySerializer

    def get_queryset(self):
        contract_type = self.request.query_params.get("contract_type")
        contract_filter = Q()
        if contract_type in {"futures", "forward", "storage"}:
            contract_filter = Q(contracts__contract_type=contract_type)

        queryset = (
            Farmer.objects
            .select_related("massive__district__region")
            .annotate(
                quantity=Coalesce(
                    Sum("contracts__planned_quantity", filter=contract_filter),
                    Decimal("0.00")
                ),
                amount=Coalesce(
                    Sum("contracts__total_amount", filter=contract_filter),
                    Decimal("0.00")
                ),
            )
        )

        if contract_type in {"futures", "forward", "storage"}:
            queryset = queryset.filter(quantity__gt=0)

        return queryset.order_by("massive__district__id", "massive__id")


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


class WarehouseSummaryAPIView(APIView):

    def get(self, request):
        receipt_rows = (
            MineralWarehouseReceipt.objects
            .values("warehouse_id", "warehouse__name", "product_id", "product__name")
            .annotate(total_in=Coalesce(Sum("quantity"), Decimal("0.00")))
        )
        expense_rows = (
            GoodsGivenItem.objects
            .values(
                "document__warehouse_id",
                "document__warehouse__name",
                "product_id",
                "product__name",
            )
            .annotate(total_out=Coalesce(Sum("quantity"), Decimal("0.00")))
        )

        warehouses_map: dict[int, str] = {}
        products_map: dict[int, str] = {}
        summary_map: dict[tuple[int, int], dict[str, Decimal]] = {}

        for row in receipt_rows:
            warehouse_id = row.get("warehouse_id")
            product_id = row.get("product_id")
            if not warehouse_id or not product_id:
                continue

            warehouses_map[warehouse_id] = row.get("warehouse__name") or "-"
            products_map[product_id] = row.get("product__name") or "-"
            summary = summary_map.setdefault(
                (warehouse_id, product_id),
                {"total_in": Decimal("0.00"), "total_out": Decimal("0.00")},
            )
            summary["total_in"] = row.get("total_in") or Decimal("0.00")

        for row in expense_rows:
            warehouse_id = row.get("document__warehouse_id")
            product_id = row.get("product_id")
            if not warehouse_id or not product_id:
                continue

            warehouses_map[warehouse_id] = row.get("document__warehouse__name") or "-"
            products_map[product_id] = row.get("product__name") or "-"
            summary = summary_map.setdefault(
                (warehouse_id, product_id),
                {"total_in": Decimal("0.00"), "total_out": Decimal("0.00")},
            )
            summary["total_out"] = row.get("total_out") or Decimal("0.00")

        products = [
            {"product_id": product_id, "product_name": products_map[product_id]}
            for product_id in sorted(products_map, key=lambda item: products_map[item])
        ]

        rows = []
        grand_totals = {
            product["product_id"]: {
                "total_in": Decimal("0.00"),
                "total_out": Decimal("0.00"),
                "balance": Decimal("0.00"),
            }
            for product in products
        }

        for index, warehouse_id in enumerate(sorted(warehouses_map, key=lambda item: warehouses_map[item]), start=1):
            warehouse_totals = []
            for product in products:
                totals = summary_map.get(
                    (warehouse_id, product["product_id"]),
                    {"total_in": Decimal("0.00"), "total_out": Decimal("0.00")},
                )
                balance = totals["total_in"] - totals["total_out"]
                warehouse_totals.append(
                    {
                        "product_id": product["product_id"],
                        "total_in": totals["total_in"],
                        "total_out": totals["total_out"],
                        "balance": balance,
                    }
                )
                grand_totals[product["product_id"]]["total_in"] += totals["total_in"]
                grand_totals[product["product_id"]]["total_out"] += totals["total_out"]
                grand_totals[product["product_id"]]["balance"] += balance

            rows.append(
                {
                    "order": index,
                    "warehouse_id": warehouse_id,
                    "warehouse_name": warehouses_map[warehouse_id],
                    "products": warehouse_totals,
                }
            )

        totals_row = {
            "warehouse_name": "Жами",
            "products": [
                {
                    "product_id": product["product_id"],
                    "total_in": grand_totals[product["product_id"]]["total_in"],
                    "total_out": grand_totals[product["product_id"]]["total_out"],
                    "balance": grand_totals[product["product_id"]]["balance"],
                }
                for product in products
            ],
        }

        return Response(
            {
                "products": products,
                "rows": rows,
                "totals": totals_row,
            }
        )


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

        if movement not in {"in", "out", "report"}:
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
                        "transport_number": item.transport_number,
                        "bag_count": item.bag_count,
                        "quantity": item.quantity,
                    }
                    for item in receipts.order_by("-date", "-id")
                ]
            )

        expense_items = GoodsGivenDocument.objects.select_related(
            "warehouse", "farmer", "farmer__massive__district"
        )

        if warehouse_id:
            expense_items = expense_items.filter(warehouse_id=warehouse_id)
        if product_id:
            expense_items = expense_items.filter(items__product_id=product_id)
        if district_id:
            expense_items = expense_items.filter(farmer__massive__district_id=district_id)

        if movement == "report":
            rows = (
                expense_items
                .values("date", "farmer__massive__district__name")
                .annotate(quantity=Coalesce(Sum("items__quantity"), Decimal("0.00")))
                .order_by("-date", "farmer__massive__district__name")
            )
            return Response(
                [
                    {
                        "date": row.get("date"),
                        "district_name": row.get("farmer__massive__district__name") or "-",
                        "quantity": row.get("quantity") or Decimal("0.00"),
                    }
                    for row in rows
                ]
            )

        rows = (
            expense_items
            .values(
                "id",
                "date",
                "warehouse__name",
                "number",
                "farmer__massive__district__name",
                "farmer__massive__name",
                "farmer__inn",
                "farmer__name",
                "farmer__maydon",
                "items__product_id",
                "items__product__name",
                "items__quantity",
                "items__price",
                "items__vat_rate",
                "items__amount",
                "items__vat_amount",
                "items__total_with_vat",
            )
            .order_by("-date", "-id", "items__product__name")
        )

        result = []
        for row in rows:
            maydon = row.get("farmer__maydon") or Decimal("0.00")
            quantity = row.get("items__quantity") or Decimal("0.00")
            quantity_per_area = Decimal("0.00")
            if maydon > 0:
                quantity_per_area = quantity / maydon

            result.append(
                {
                    "id": row.get("id"),
                    "date": row.get("date"),
                    "warehouse_name": row.get("warehouse__name") or "-",
                    "number": row.get("number") or "-",
                    "district_name": row.get("farmer__massive__district__name") or "-",
                    "massive_name": row.get("farmer__massive__name") or "-",
                    "inn": row.get("farmer__inn") or "-",
                    "farmer_name": row.get("farmer__name") or "-",
                    "product_id": row.get("items__product_id"),
                    "product_name": row.get("items__product__name") or "-",
                    "quantity": quantity,
                    "price": row.get("items__price") or Decimal("0.00"),
                    "vat_rate": row.get("items__vat_rate") or "0",
                    "amount": row.get("items__amount") or Decimal("0.00"),
                    "vat_amount": row.get("items__vat_amount") or Decimal("0.00"),
                    "total_with_vat": row.get("items__total_with_vat") or Decimal("0.00"),
                    "maydon": maydon,
                    "quantity_per_area": quantity_per_area,
                }
            )

        return Response(result)




class BotUserActivityAnalyticsAPIView(APIView):

    def get(self, request):
        user_id = request.query_params.get("user_id")

        activities = BotUserActivity.objects.select_related("user")
        if user_id:
            activities = activities.filter(user_id=user_id)

        users_summary = []
        grouped_users = (
            activities
            .values("user_id", "user__full_name", "user__telegram_id")
            .annotate(
                first_activity=Min("created_at"),
                last_activity=Max("created_at"),
                actions_count=Count("id"),
            )
            .order_by("user__full_name")
        )

        for row in grouped_users:
            first_activity = row.get("first_activity")
            last_activity = row.get("last_activity")
            active_seconds = 0
            if first_activity and last_activity:
                active_seconds = int((last_activity - first_activity).total_seconds())

            users_summary.append({
                "user_id": row.get("user_id"),
                "full_name": row.get("user__full_name") or "-",
                "telegram_id": row.get("user__telegram_id"),
                "first_activity": first_activity,
                "last_activity": last_activity,
                "actions_count": row.get("actions_count") or 0,
                "active_seconds": active_seconds,
            })

        timeline = [
            {
                "id": item.id,
                "user_id": item.user_id,
                "full_name": item.user.full_name if item.user else "-",
                "telegram_id": item.user.telegram_id if item.user else None,
                "action_type": item.action_type,
                "action_name": item.action_name,
                "action_payload": item.action_payload,
                "is_allowed": item.is_allowed,
                "created_at": item.created_at,
            }
            for item in activities.order_by("-created_at")[:500]
        ]

        by_hour = [
            {
                "hour": hour,
                "actions_count": sum(1 for item in timeline if item["created_at"].hour == hour),
            }
            for hour in range(24)
        ]

        return Response({
            "users": users_summary,
            "timeline": timeline,
            "by_hour": by_hour,
        })

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

        if user.full_name != full_name and full_name:
            user.full_name = full_name
            user.save(update_fields=["full_name"])

        BotUserActivity.objects.create(
            user=user,
            action_type=BotUserActivity.ACTION_SYSTEM,
            action_name="access_check",
            action_payload="/start access validation",
            is_allowed=user.is_active,
        )

        return Response({
            "allowed": user.is_active,
            "created": created
        })


class BotUserActivityCreateAPIView(APIView):

    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        if not telegram_id:
            return Response({"created": False}, status=400)

        user = BotUser.objects.filter(telegram_id=telegram_id).first()
        if not user:
            return Response({"created": False}, status=404)

        action_type = request.data.get("action_type") or BotUserActivity.ACTION_MESSAGE
        action_name = (request.data.get("action_name") or "unknown")[:100]
        action_payload = (request.data.get("action_payload") or "")
        raw_is_allowed = request.data.get("is_allowed", True)
        if isinstance(raw_is_allowed, str):
            is_allowed = raw_is_allowed.strip().lower() in {"1", "true", "yes", "y"}
        else:
            is_allowed = bool(raw_is_allowed)

        BotUserActivity.objects.create(
            user=user,
            action_type=action_type,
            action_name=action_name,
            action_payload=action_payload[:1000],
            is_allowed=is_allowed,
        )

        return Response({"created": True})
