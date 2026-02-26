from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from query.models.contracts import Contract
from query.models.counterparties import Farmer
from query.models.documents import GoodsGivenDocument, GoodsGivenItem, Warehouse
from query.models.reference import District, Massive, Product, Region, Unit


class WarehouseReportMovementsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        unit = Unit.objects.create(name="Kilogram", short_name="kg")
        self.product = Product.objects.create(name="Selitra", unit=unit)

        region = Region.objects.create(name="Toshkent")
        district = District.objects.create(region=region, name="Yangiyul")
        massive = Massive.objects.create(district=district, name="Massiv-1")

        self.farmer = Farmer.objects.create(
            name="Farmer 1",
            inn="123456789",
            massive=massive,
            maydon=Decimal("10.00"),
        )
        self.warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.contract = Contract.objects.create(
            farmer=self.farmer,
            number="C-1",
            date="2026-01-01",
            planned_quantity=Decimal("100.00"),
            price=Decimal("1000.00"),
        )

    def test_report_includes_date_and_separates_daily_and_total_values(self):
        today = "2026-02-01"
        previous_day = "2026-01-31"

        doc_today = GoodsGivenDocument.objects.create(
            date=today,
            number="G-1",
            farmer=self.farmer,
            contract=self.contract,
            warehouse=self.warehouse,
        )
        GoodsGivenItem.objects.create(
            document=doc_today,
            product=self.product,
            quantity=Decimal("200.00"),
            price=Decimal("1.00"),
        )

        doc_previous = GoodsGivenDocument.objects.create(
            date=previous_day,
            number="G-2",
            farmer=self.farmer,
            contract=self.contract,
            warehouse=self.warehouse,
        )
        GoodsGivenItem.objects.create(
            document=doc_previous,
            product=self.product,
            quantity=Decimal("400.00"),
            price=Decimal("1.00"),
        )

        response = self.client.get(
            "/api/warehouse/movements/",
            {
                "movement": "report",
                "warehouse_id": self.warehouse.id,
                "product_id": self.product.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        returned_dates = {str(item["date"]) for item in response.data}
        self.assertSetEqual(returned_dates, {today, previous_day})

        quantities_by_date = {str(item["date"]): Decimal(str(item["quantity"])) for item in response.data}
        self.assertEqual(quantities_by_date[today], Decimal("200.00"))
        self.assertEqual(quantities_by_date[previous_day], Decimal("400.00"))
