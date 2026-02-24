from django.db import models
from .counterparties import Farmer
from django.db.models import Sum
from decimal import Decimal
#====================================================================================================================
#=                                                                                                                 =#
#====================================================================================================================
class Contract(models.Model):
    farmer = models.ForeignKey(Farmer,on_delete=models.CASCADE,related_name="contracts",verbose_name="Фермер")
    number = models.CharField("Шартнома рақами",max_length=100)
    date = models.DateField("Шартнома санаси")
    planned_quantity = models.DecimalField("Режадаги миқдор (тонна)",max_digits=12,decimal_places=2)
    price = models.DecimalField("1 тонна нархи",max_digits=14,decimal_places=2)
    total_amount = models.DecimalField("Жами сумма",max_digits=16,decimal_places=2,default=0)
    is_active = models.BooleanField("Фаол", default=True)

    class Meta:
        verbose_name = "Шартнома"
        verbose_name_plural = "Шартномалар"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["farmer", "number"],
                name="unique_contract_per_farmer"
            )
        ]
    @property
    def balance(self):
        totals = self.ledgers.aggregate(
            total_debit=Sum("debit"),
            total_credit=Sum("credit")
        )
        debit = totals["total_debit"] or Decimal("0.00")
        credit = totals["total_credit"] or Decimal("0.00")
        return debit - credit    

    def save(self, *args, **kwargs):
        self.total_amount = self.planned_quantity * self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"№-{self.number} от {self.date}"

#========================================================================================



