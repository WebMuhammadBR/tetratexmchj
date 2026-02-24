from django.db import models
from .reference import Massive
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal

#================================================================================================================
#--         FARMER                                                                                            --#
#================================================================================================================
class Farmer(models.Model):
    name = models.CharField("Фермер номи", max_length=255)
    inn = models.CharField("ИНН",max_length=20,unique=True)
    maydon = models.DecimalField("Майдон", max_digits=12, decimal_places=2, blank=True, null=True)
    massive = models.ForeignKey(Massive,on_delete=models.SET_NULL,null=True,blank=True,verbose_name="Массив")
    is_active = models.BooleanField("Фаол", default=True)

    class Meta:
        verbose_name = "Фермер"
        verbose_name_plural = "Фермерлар"
        ordering = ["name"]

    @property
    def balance(self):
        totals = self.ledgers.aggregate(
            total_debit=Sum("debit"),
            total_credit=Sum("credit")
        )
        debit = totals["total_debit"] or Decimal("0.00")
        credit = totals["total_credit"] or Decimal("0.00")
        return debit - credit    

    def __str__(self):
        return f"{self.name} ({self.inn})"
    
#================================================================================================================
#--         BANK                                                                                              --#
#================================================================================================================
class BankAccount(models.Model):
    farmer = models.ForeignKey(Farmer,on_delete=models.CASCADE,related_name="bank_accounts",verbose_name="Фермер")
    bank_name = models.CharField("Банк номи", max_length=255)
    account_number = models.CharField("Ҳисоб рақами", max_length=50)
    mfo = models.CharField("МФО", max_length=10)
    is_main = models.BooleanField("Асосий ҳисоб", default=False)

    class Meta:
        verbose_name = "Банк ҳисоб рақами"
        verbose_name_plural = "Банк ҳисоб рақамлари"
        constraints = [
            models.UniqueConstraint(
                fields=["farmer"],
                condition=models.Q(is_main=True),
                name="unique_main_account_per_farmer"
            )
        ]

    def clean(self):
        if not self.farmer_id:
            return  # Farmer ҳали сақланмаган

        if self.is_main:
            exists = BankAccount.objects.filter(
                farmer_id=self.farmer_id,
                is_main=True
            ).exclude(pk=self.pk).exists()

            if exists:
                raise ValidationError(
                    "Бу фермерда аллақачон асосий ҳисоб рақам мавжуд!"
                )

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"
#=======================================================================================
