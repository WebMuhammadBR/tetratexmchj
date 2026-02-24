from django.urls import path

from .views import (
    FarmerListAPIView,
    FarmerSummaryAPIView,
    BotUserCheckAPIView,
    MineralWarehouseReceiptListAPIView,
    GoodsGivenDocumentListAPIView,
    MineralWarehouseTotalsAPIView,
    WarehouseListAPIView,
    WarehouseProductsAPIView,
    WarehouseMovementsAPIView,
    WarehouseExpenseDistrictsAPIView,
)

urlpatterns = [
    path("farmers/", FarmerListAPIView.as_view(), name="api_farmers"),
    path("farmers/summary/", FarmerSummaryAPIView.as_view()),
    path("warehouse/totals/", MineralWarehouseTotalsAPIView.as_view()),
    path("warehouse/list/", WarehouseListAPIView.as_view()),
    path("warehouse/receipts/", MineralWarehouseReceiptListAPIView.as_view()),
    path("warehouse/expenses/", GoodsGivenDocumentListAPIView.as_view()),
    path("warehouse/products/", WarehouseProductsAPIView.as_view()),
    path("warehouse/expense-districts/", WarehouseExpenseDistrictsAPIView.as_view()),
    path("warehouse/movements/", WarehouseMovementsAPIView.as_view()),
    path("bot-user/check/", BotUserCheckAPIView.as_view()),
]
