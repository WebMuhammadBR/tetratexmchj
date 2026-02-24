from django.db import models
from .counterparties import Farmer
from decimal import Decimal
from django.db import models
from .contracts import Contract
from django.db.models import Sum

# ==========================================
# DOCUMENT (Шапка)   ПАХТА
# ==========================================
    

class GoodsReceivedDocument(models.Model):
    date = models.DateField("Сана")
    number = models.CharField("Ҳужжат рақами", max_length=50)
    farmer = models.ForeignKey(Farmer,on_delete=models.PROTECT,verbose_name="Фермер")
    contract = models.ForeignKey(Contract,on_delete=models.PROTECT,verbose_name="Шартнома")

    class Meta:
        verbose_name = "Пахта қабул ҳужжати"
        verbose_name_plural = "Пахта қабул ҳужжатлари"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["farmer", "number"],
                name="unique_received_number_per_farmer"
            )
        ]

    @property
    def total_amount(self):
        total = self.received_items.aggregate(
            total=Sum("amount")
        )["total"]

        return total or Decimal("0.00")
    def __str__(self):
        return f"{self.number} - {self.farmer}"

#====================================================================
# Пахта кабули накладнойи
#====================================================================
class GoodsReceivedItem(models.Model):
    document = models.ForeignKey(GoodsReceivedDocument,on_delete=models.CASCADE,related_name="received_items",verbose_name="Пахта қабул ҳужжати")
    physical_weight = models.DecimalField("Физик вазн",max_digits=12,decimal_places=2)
    impurity = models.DecimalField("Ифлослик %",max_digits=4,decimal_places=1)
    calculated_weight = models.DecimalField("Ҳисобий вазн",max_digits=12,decimal_places=2,default=0)
    moisture = models.DecimalField("Намлик %",max_digits=4,decimal_places=1)
    conditional_weight = models.DecimalField("Кондицион вазн",max_digits=12,decimal_places=2,default=0)
    selection_type = models.ForeignKey("SelectionType",on_delete=models.PROTECT,verbose_name="Селекцион нав")
    sort_class = models.ForeignKey("SortClass",on_delete=models.PROTECT,verbose_name="Сорт / Класс")
    price = models.DecimalField("Нарх",max_digits=14,decimal_places=2,default=0)
    amount = models.DecimalField("Сумма",max_digits=16,decimal_places=2,default=0)

    class Meta:
        verbose_name = "Қабул қилинган пахта"
        verbose_name_plural = "Қабул қилинган пахталар"

    def save(self, *args, **kwargs):

        # ==============================
        # 1️⃣ Ҳисобий вазн
        # ==============================
        self.calculated_weight = (
            self.physical_weight * (Decimal("100") - self.impurity) / Decimal("98")
        )
        # ==============================
        # 2️⃣ Кондицион вазн
        # ==============================
        self.conditional_weight = (
            self.calculated_weight * (Decimal("109") / (Decimal("100") + self.moisture))
        )
        # ==============================
        # 3️⃣ Нарх ҳисоблаш
        # ==============================
        contract_price = self.document.contract.price
        self.price = (contract_price* self.selection_type.coefficient* self.sort_class.coefficient)
        # ==============================
        # 4️⃣ Сумма
        # ==============================
        self.amount = self.price * self.conditional_weight

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.document.number} | {self.conditional_weight} кг"

#====================================================================
#  Пахтанинг селекцион нави (Анд-35,Анд-36)
#====================================================================

class SelectionType(models.Model):
    TYPE_CHOICES = [(i, str(i)) for i in range(1, 10)]
    name = models.CharField("Номи", max_length=100)
    type = models.IntegerField("Типи",choices=TYPE_CHOICES)
    coefficient = models.DecimalField("Коэффициент",max_digits=5,decimal_places=4)

    class Meta:
        verbose_name = "Селекцион нав"
        verbose_name_plural = "Селекцион навлар"

    def __str__(self):
        return f"{self.name} (тип {self.type})"
#====================================================================
# Пахтанинг Сорт класси (1-сорт 1-класс)
#====================================================================
class SortClass(models.Model):
    SORT_CHOICES = [(i, str(i)) for i in range(1, 6)]
    CLASS_CHOICES = [(i, str(i)) for i in range(1, 4)]

    sort = models.IntegerField("Сорт", choices=SORT_CHOICES)
    class_grade = models.IntegerField("Класс", choices=CLASS_CHOICES)
    coefficient = models.DecimalField("Коэффициент",max_digits=5,decimal_places=3)

    class Meta:
        verbose_name = "Сорт/Класс"
        verbose_name_plural = "Сорт/Класслар"
        unique_together = ("sort", "class_grade")

    def __str__(self):
        return f"{self.sort}-сорт / {self.class_grade}-класс"
