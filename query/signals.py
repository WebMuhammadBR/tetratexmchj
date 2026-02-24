from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from .models.documents import GoodsGivenItem
from .models.accounting import Ledger
from .models.cotton import GoodsReceivedItem

# ==========================================
# 🔵 GOODS GIVEN  → DEBIT
# ==========================================

def update_given_ledger(document):
    Ledger.objects.filter(given_document=document).delete()

    total = document.total_amount

    if total > 0:
        Ledger.objects.create(
            farmer=document.farmer,
            contract=document.contract,
            given_document=document,
            debit=total,
            credit=Decimal("0.00"),
            date=document.date
        )


@receiver(post_save, sender=GoodsGivenItem)
def given_item_saved(sender, instance, **kwargs):
    update_given_ledger(instance.document)


@receiver(post_delete, sender=GoodsGivenItem)
def given_item_deleted(sender, instance, **kwargs):
    update_given_ledger(instance.document)


# ==========================================
# 🟢 GOODS RECEIVED  → CREDIT
# ==========================================

def update_received_ledger(document):
    Ledger.objects.filter(received_document=document).delete()

    total = document.total_amount

    if total > 0:
        Ledger.objects.create(
            farmer=document.farmer,
            contract=document.contract,
            received_document=document,
            debit=Decimal("0.00"),
            credit=total,
            date=document.date
        )


@receiver(post_save, sender=GoodsReceivedItem)
def received_item_saved(sender, instance, **kwargs):
    update_received_ledger(instance.document)


@receiver(post_delete, sender=GoodsReceivedItem)
def received_item_deleted(sender, instance, **kwargs):
    update_received_ledger(instance.document)
