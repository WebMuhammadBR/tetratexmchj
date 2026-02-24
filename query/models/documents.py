from django.db import models
from .counterparties import Farmer
from .contracts import Contract
from decimal import Decimal
from .reference import Product
from django.db.models import Sum


class Warehouse(models.Model):
    name = models.CharField("Омбор номи", max_length=255, unique=True)

    class Meta:
        verbose_name = "Омбор"
        verbose_name_plural = "Омборлар"
        ordering = ["name"]

    def __str__(self):
        return self.name


class MineralWarehouseReceipt(models.Model):
    class TransportType(models.TextChoices):
        TRUCK = "truck", "Юк машинаси"
        TRACTOR = "tractor", "Трактор"
        TRAIN = "train", "Поезд"
        OTHER = "other", "Бошқа"

    date = models.DateField("Сана")
    invoice_number = models.CharField("Накладной рақами", max_length=50)
    transport_type = models.CharField(
        "Транспорт русуми",
        max_length=20,
        choices=TransportType.choices,
    )
    transport_number = models.CharField("Транспорт рақами", max_length=30)
    bag_count = models.PositiveIntegerField("Қоп сони", default=0)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Маҳсулот", null=True, blank=True)
    quantity = models.DecimalField("Миқдори", max_digits=14, decimal_places=2)
    price = models.DecimalField("Нарх", max_digits=14, decimal_places=2, default=0)
    amount = models.DecimalField("Сумма", max_digits=14, decimal_places=2, default=0)
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="receipts",
        verbose_name="Омбор",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Омбор кирим ҳужжати"
        verbose_name_plural = "Омбор кирим ҳужжатлари"
        ordering = ["-date", "-id"]

    def __str__(self):
        warehouse_name = self.warehouse.name if self.warehouse else "-"
        return f"{warehouse_name} / {self.invoice_number}"

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.price
        super().save(*args, **kwargs)

# ==========================================
# DOCUMENT (Шапка) Тавар
# ==========================================
class GoodsGivenDocument(models.Model):
    date = models.DateField("Сана")
    number = models.CharField("Ҳужжат рақами", max_length=50)
    farmer = models.ForeignKey(Farmer,on_delete=models.PROTECT,verbose_name="Фермер")
    contract = models.ForeignKey(Contract,on_delete=models.PROTECT,verbose_name="Шартнома")
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="given_documents",
        verbose_name="Омбор",
    )

    class Meta:
        verbose_name = "Товар бериш ҳужжати"
        verbose_name_plural = "Товар бериш ҳужжатлари"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["farmer", "number"],
                name="unique_given_number_per_farmer"
            )
        ]    

    @property
    def total_amount(self):
        total = self.items.aggregate(
            total=Sum("total_with_vat")
        )["total"]

        return total or Decimal("0.00")
    
    
    
    
    
    def __str__(self):
        return f"{self.number} - {self.farmer}"


# ========================================================================================
# DOCUMENT ITEM (Позиция)
# ========================================================================================


class GoodsGivenItem(models.Model):
    VAT_CHOICES = (
        ("0", "Без НДС"),
        ("12", "12%"),
        ("15", "15%"),
    )
    document = models.ForeignKey(GoodsGivenDocument,on_delete=models.CASCADE,related_name="items",verbose_name="Товар бериш ҳужжати")
    product = models.ForeignKey(Product,on_delete=models.PROTECT,verbose_name="Маҳсулот")
    quantity = models.DecimalField("Миқдори", max_digits=12, decimal_places=2)
    price = models.DecimalField("Нарх", max_digits=14, decimal_places=2)
    amount = models.DecimalField("Сумма", max_digits=14, decimal_places=2, default=0)
    vat_rate = models.CharField("НДС ставкаси",max_length=5,choices=VAT_CHOICES,default="12")
    vat_amount = models.DecimalField("НДС суммаси", max_digits=14, decimal_places=2, default=0)
    total_with_vat = models.DecimalField("Жами сумма", max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Товар бериш позицияси"
        verbose_name_plural = "Товар бериш позициялари"

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.price
        vat_percent = Decimal(self.vat_rate)
        if vat_percent > 0:
            self.vat_amount = (self.amount * vat_percent) / Decimal("100")
        else:
            self.vat_amount = Decimal("0.00")
        self.total_with_vat = self.amount + self.vat_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} ({self.quantity})"

#====================================================================
#====================================================================
