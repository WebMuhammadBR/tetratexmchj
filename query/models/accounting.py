from django.db import models
from .counterparties import Farmer
from .documents import GoodsGivenDocument
from .cotton import GoodsReceivedDocument
from .contracts import Contract


class Ledger(models.Model):

    farmer = models.ForeignKey(Farmer,on_delete=models.CASCADE,related_name="ledgers")
    contract = models.ForeignKey(Contract,on_delete=models.CASCADE,related_name="ledgers")
    given_document = models.ForeignKey(GoodsGivenDocument,on_delete=models.CASCADE,null=True,blank=True)
    received_document = models.ForeignKey(GoodsReceivedDocument,on_delete=models.CASCADE,null=True,blank=True)
    debit = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    date = models.DateField()


    class Meta:
        verbose_name = "Ҳаракат журнали"
        verbose_name_plural = "Ҳаракат журнали"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.farmer} | D:{self.debit} C:{self.credit}"
