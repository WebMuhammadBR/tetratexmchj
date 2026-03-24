from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient
from tgbot.handlers.mineral import _aggregate_expense_rows_by_farmer

from query.models.bot import BotUser, BotUserActivity
from query.models.contracts import Contract
from query.models.counterparties import Farmer
from query.models.documents import GoodsGivenDocument, GoodsGivenItem, MineralWarehouseReceipt, Warehouse
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

    def test_out_movements_include_district_massive_and_farmer_fields(self):
        doc = GoodsGivenDocument.objects.create(
            date="2026-02-02",
            number="YH-10",
            farmer=self.farmer,
            contract=self.contract,
            warehouse=self.warehouse,
        )
        GoodsGivenItem.objects.create(
            document=doc,
            product=self.product,
            quantity=Decimal("250.00"),
            price=Decimal("1.00"),
        )

        response = self.client.get(
            "/api/warehouse/movements/",
            {
                "movement": "out",
                "warehouse_id": self.warehouse.id,
                "product_id": self.product.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["district_name"], "Yangiyul")
        self.assertEqual(response.data[0]["massive_name"], "Massiv-1")
        self.assertEqual(response.data[0]["inn"], self.farmer.inn)
        self.assertEqual(response.data[0]["farmer_name"], "Farmer 1")
        self.assertEqual(response.data[0]["number"], "YH-10")
        self.assertEqual(Decimal(str(response.data[0]["price"])), Decimal("1.00"))
        self.assertEqual(response.data[0]["vat_rate"], "12")
        self.assertEqual(Decimal(str(response.data[0]["amount"])), Decimal("250.00"))
        self.assertEqual(Decimal(str(response.data[0]["vat_amount"])), Decimal("30.00"))
        self.assertEqual(Decimal(str(response.data[0]["total_with_vat"])), Decimal("280.00"))


class WarehouseReceiptMovementsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        unit = Unit.objects.create(name="Kilogram", short_name="kg")
        self.product = Product.objects.create(name="Selitra", unit=unit)
        self.warehouse = Warehouse.objects.create(name="Main Warehouse")

    def test_in_movements_include_transport_and_warehouse(self):
        MineralWarehouseReceipt.objects.create(
            date="2026-03-01",
            invoice_number="INV-777",
            transport_type="truck",
            transport_number="01A123BC",
            bag_count=30,
            product=self.product,
            quantity=Decimal("1500.00"),
            price=Decimal("100.00"),
            warehouse=self.warehouse,
        )

        response = self.client.get(
            "/api/warehouse/movements/",
            {
                "movement": "in",
                "warehouse_id": self.warehouse.id,
                "product_id": self.product.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["invoice_number"], "INV-777")
        self.assertEqual(response.data[0]["transport_number"], "01A123BC")
        self.assertEqual(response.data[0]["warehouse_name"], "Main Warehouse")


class BotUserActivityAnalyticsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = BotUser.objects.create(
            telegram_id=99887766,
            full_name="Test User",
            is_active=True,
        )

    def test_analytics_returns_users_timeline_and_hours(self):
        BotUserActivity.objects.create(
            user=self.user,
            action_type=BotUserActivity.ACTION_MESSAGE,
            action_name="start_handler",
            action_payload="/start",
            is_allowed=True,
        )
        BotUserActivity.objects.create(
            user=self.user,
            action_type=BotUserActivity.ACTION_CALLBACK,
            action_name="contracts_menu",
            action_payload="contracts",
            is_allowed=True,
        )

        response = self.client.get('/api/bot-user/activity/analytics/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['users']), 1)
        self.assertEqual(response.data['users'][0]['actions_count'], 2)
        self.assertEqual(len(response.data['timeline']), 2)
        self.assertEqual(len(response.data['by_hour']), 24)

    def test_create_activity_endpoint_logs_event(self):
        response = self.client.post(
            '/api/bot-user/activity/',
            {
                'telegram_id': self.user.telegram_id,
                'action_type': 'message',
                'action_name': 'farmers_menu',
                'action_payload': '📋 Фермерлар',
                'is_allowed': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(BotUserActivity.objects.filter(user=self.user, action_name='farmers_menu').exists())


class FarmerSummaryContractTypeFilterAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        region = Region.objects.create(name="Toshkent")
        district = District.objects.create(region=region, name="Yangiyul")
        massive = Massive.objects.create(district=district, name="Massiv-1")

        self.farmer = Farmer.objects.create(
            name="Farmer Filter",
            inn="987654321",
            massive=massive,
            maydon=Decimal("5.00"),
        )

        Contract.objects.create(
            farmer=self.farmer,
            number="FUT-1",
            contract_type="futures",
            date="2026-01-01",
            planned_quantity=Decimal("100.00"),
            price=Decimal("1000.00"),
        )
        Contract.objects.create(
            farmer=self.farmer,
            number="FWD-1",
            contract_type="forward",
            date="2026-01-02",
            planned_quantity=Decimal("50.00"),
            price=Decimal("2000.00"),
        )

    def test_summary_filters_by_contract_type(self):
        response = self.client.get('/api/farmers/summary/', {'contract_type': 'forward'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(Decimal(str(response.data[0]['quantity'])), Decimal('50.00'))
        self.assertEqual(Decimal(str(response.data[0]['amount'])), Decimal('100000.00'))



class FarmerSummaryAggregationRegressionAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        region = Region.objects.create(name="Buxoro")
        district = District.objects.create(region=region, name="G'ijduvon")
        massive = Massive.objects.create(district=district, name="Massiv-2")

        self.farmer = Farmer.objects.create(
            name="XOJI SULTON ALI FX",
            inn="307221416",
            massive=massive,
            maydon=Decimal("10.00"),
        )

        Contract.objects.create(
            farmer=self.farmer,
            number="CNT-1",
            contract_type="forward",
            date="2026-03-01",
            planned_quantity=Decimal("5779.00"),
            price=Decimal("1.00"),
        )
        Contract.objects.create(
            farmer=self.farmer,
            number="CNT-2",
            contract_type="forward",
            date="2026-03-02",
            planned_quantity=Decimal("16000.00"),
            price=Decimal("1.00"),
        )
        Contract.objects.create(
            farmer=self.farmer,
            number="CNT-3",
            contract_type="forward",
            date="2026-03-03",
            planned_quantity=Decimal("112495.00"),
            price=Decimal("1.00"),
        )

    def test_summary_does_not_multiply_quantity_when_farmer_has_multiple_same_type_contracts(self):
        response = self.client.get('/api/farmers/summary/', {'contract_type': 'forward'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(Decimal(str(response.data[0]['quantity'])), Decimal('134274.00'))

class FarmerListAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        region = Region.objects.create(name="Samarqand")
        district = District.objects.create(region=region, name="Pastdargom")
        massive = Massive.objects.create(district=district, name="Massiv-7")

        self.farmer = Farmer.objects.create(
            name="Farmer List",
            inn="111222333",
            massive=massive,
            maydon=Decimal("12.00"),
        )

        Contract.objects.create(
            farmer=self.farmer,
            number="CNT-77",
            contract_type="futures",
            date="2026-01-10",
            planned_quantity=Decimal("12.00"),
            price=Decimal("1000.00"),
        )

    def test_list_contains_contract_district_and_massive(self):
        response = self.client.get('/api/farmers/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['contract'], 'CNT-77')
        self.assertEqual(response.data[0]['district'], 'Pastdargom')
        self.assertEqual(response.data[0]['massive'], 'Massiv-7')


class FarmerListProductTotalsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        region = Region.objects.create(name="Jizzax")
        district = District.objects.create(region=region, name="Gallaorol")
        massive = Massive.objects.create(district=district, name="Massiv-9")

        self.farmer = Farmer.objects.create(
            name="Farmer Totals",
            inn="123123123",
            massive=massive,
            maydon=Decimal("20.00"),
        )

        self.contract = Contract.objects.create(
            farmer=self.farmer,
            number="CNT-99",
            contract_type="futures",
            date="2026-01-15",
            planned_quantity=Decimal("40.00"),
            price=Decimal("1000.00"),
        )

        self.warehouse = Warehouse.objects.create(name="Totals Warehouse")
        unit = Unit.objects.create(name="Dona", short_name="d")
        self.product_1 = Product.objects.create(name="Ammofos", unit=unit)
        self.product_2 = Product.objects.create(name="Karbamid", unit=unit)
        self.product_3 = Product.objects.create(name="Selitra", unit=unit)

        self.second_farmer = Farmer.objects.create(
            name="Farmer Without Product",
            inn="321321321",
            massive=massive,
            maydon=Decimal("8.00"),
        )

        Contract.objects.create(
            farmer=self.second_farmer,
            number="CNT-100",
            contract_type="futures",
            date="2026-01-16",
            planned_quantity=Decimal("25.00"),
            price=Decimal("1000.00"),
        )

    def test_list_contains_product_totals_and_farmer_total_amount(self):
        document = GoodsGivenDocument.objects.create(
            date="2026-02-10",
            number="GD-100",
            farmer=self.farmer,
            contract=self.contract,
            warehouse=self.warehouse,
        )

        GoodsGivenItem.objects.create(
            document=document,
            product=self.product_1,
            quantity=Decimal("10.00"),
            price=Decimal("20.00"),
        )
        GoodsGivenItem.objects.create(
            document=document,
            product=self.product_2,
            quantity=Decimal("5.00"),
            price=Decimal("30.00"),
        )

        response = self.client.get('/api/farmers/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        item = next(row for row in response.data if row['name'] == 'Farmer Totals')
        self.assertEqual(Decimal(str(item['product_totals']['Ammofos'])), Decimal('224.00'))
        self.assertEqual(Decimal(str(item['product_totals']['Karbamid'])), Decimal('168.00'))
        self.assertEqual(Decimal(str(item['product_totals']['Selitra'])), Decimal('0.00'))
        self.assertEqual(Decimal(str(item['farmer_total_amount'])), Decimal('392.00'))

    def test_list_contains_all_active_products_with_zero_for_missing_items(self):
        response = self.client.get('/api/farmers/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        first = response.data[0]
        second = response.data[1]

        self.assertSetEqual(
            set(first['product_totals'].keys()),
            {'Ammofos', 'Karbamid', 'Selitra'},
        )
        self.assertSetEqual(
            set(second['product_totals'].keys()),
            {'Ammofos', 'Karbamid', 'Selitra'},
        )

        self.assertEqual(Decimal(str(second['product_totals']['Ammofos'])), Decimal('0.00'))
        self.assertEqual(Decimal(str(second['product_totals']['Karbamid'])), Decimal('0.00'))
        self.assertEqual(Decimal(str(second['product_totals']['Selitra'])), Decimal('0.00'))
        self.assertEqual(Decimal(str(second['farmer_total_amount'])), Decimal('0.00'))


class WarehouseExpenseAggregationTest(TestCase):
    def test_aggregate_recalculates_quantity_per_area_from_total_quantity(self):
        rows = [
            {
                "district_name": "Yangiyul",
                "massive_name": "Massiv-1",
                "farmer_name": "Farmer 1",
                "product_name": "Selitra",
                "quantity": 100,
                "maydon": 1,
                "quantity_per_area": 100,
            },
            {
                "district_name": "Yangiyul",
                "massive_name": "Massiv-1",
                "farmer_name": "Farmer 1",
                "product_name": "Selitra",
                "quantity": 100,
                "maydon": 1,
                "quantity_per_area": 100,
            },
            {
                "district_name": "Yangiyul",
                "massive_name": "Massiv-1",
                "farmer_name": "Farmer 1",
                "product_name": "Selitra",
                "quantity": 100,
                "maydon": 1,
                "quantity_per_area": 100,
            },
        ]

        aggregated = _aggregate_expense_rows_by_farmer(rows)

        self.assertEqual(len(aggregated), 1)
        self.assertEqual(aggregated[0]["quantity"], 300)
        self.assertEqual(aggregated[0]["quantity_per_area"], 300)


class WarehouseSummaryAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        unit = Unit.objects.create(name="Kilogram", short_name="kg")
        self.product_1 = Product.objects.create(name="Ammofos", unit=unit)
        self.product_2 = Product.objects.create(name="Karbamid", unit=unit)

        region = Region.objects.create(name="Samarqand")
        district = District.objects.create(region=region, name="Urgut")
        massive = Massive.objects.create(district=district, name="Massiv-7")

        self.farmer = Farmer.objects.create(
            name="Farmer Summary",
            inn="111222333",
            massive=massive,
            maydon=Decimal("12.00"),
        )
        self.contract = Contract.objects.create(
            farmer=self.farmer,
            number="CNT-SUM-1",
            date="2026-01-20",
            planned_quantity=Decimal("90.00"),
            price=Decimal("1500.00"),
        )
        self.warehouse_1 = Warehouse.objects.create(name="Ombor 1")
        self.warehouse_2 = Warehouse.objects.create(name="Ombor 2")

    def test_summary_returns_product_columns_rows_and_grand_totals(self):
        MineralWarehouseReceipt.objects.create(
            date="2026-02-01",
            warehouse=self.warehouse_1,
            product=self.product_1,
            invoice_number="IN-1",
            transport_number="01A111AA",
            bag_count=10,
            quantity=Decimal("100.00"),
            price=Decimal("1.00"),
            amount=Decimal("100.00"),
        )
        MineralWarehouseReceipt.objects.create(
            date="2026-02-02",
            warehouse=self.warehouse_2,
            product=self.product_1,
            invoice_number="IN-2",
            transport_number="01A222AA",
            bag_count=12,
            quantity=Decimal("50.00"),
            price=Decimal("1.00"),
            amount=Decimal("50.00"),
        )
        MineralWarehouseReceipt.objects.create(
            date="2026-02-03",
            warehouse=self.warehouse_2,
            product=self.product_2,
            invoice_number="IN-3",
            transport_number="01A333AA",
            bag_count=8,
            quantity=Decimal("80.00"),
            price=Decimal("1.00"),
            amount=Decimal("80.00"),
        )

        doc_1 = GoodsGivenDocument.objects.create(
            date="2026-02-04",
            number="OUT-1",
            farmer=self.farmer,
            contract=self.contract,
            warehouse=self.warehouse_1,
        )
        GoodsGivenItem.objects.create(
            document=doc_1,
            product=self.product_1,
            quantity=Decimal("25.00"),
            price=Decimal("1.00"),
        )

        doc_2 = GoodsGivenDocument.objects.create(
            date="2026-02-05",
            number="OUT-2",
            farmer=self.farmer,
            contract=self.contract,
            warehouse=self.warehouse_2,
        )
        GoodsGivenItem.objects.create(
            document=doc_2,
            product=self.product_2,
            quantity=Decimal("30.00"),
            price=Decimal("1.00"),
        )

        response = self.client.get("/api/warehouse/summary/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["product_name"] for item in response.data["products"]], ["Ammofos", "Karbamid"])
        self.assertEqual([item["warehouse_name"] for item in response.data["rows"]], ["Ombor 1", "Ombor 2"])

        first_row = response.data["rows"][0]
        first_product = next(item for item in first_row["products"] if item["product_id"] == self.product_1.id)
        self.assertEqual(Decimal(str(first_product["total_in"])), Decimal("100.00"))
        self.assertEqual(Decimal(str(first_product["total_out"])), Decimal("25.00"))
        self.assertEqual(Decimal(str(first_product["balance"])), Decimal("75.00"))

        totals_product_1 = next(
            item for item in response.data["totals"]["products"] if item["product_id"] == self.product_1.id
        )
        totals_product_2 = next(
            item for item in response.data["totals"]["products"] if item["product_id"] == self.product_2.id
        )
        self.assertEqual(Decimal(str(totals_product_1["total_in"])), Decimal("150.00"))
        self.assertEqual(Decimal(str(totals_product_1["total_out"])), Decimal("25.00"))
        self.assertEqual(Decimal(str(totals_product_1["balance"])), Decimal("125.00"))
        self.assertEqual(Decimal(str(totals_product_2["total_in"])), Decimal("80.00"))
        self.assertEqual(Decimal(str(totals_product_2["total_out"])), Decimal("30.00"))
        self.assertEqual(Decimal(str(totals_product_2["balance"])), Decimal("50.00"))
