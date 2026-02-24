from django.db import models


# ===============================
# UNIT (Ўлчов бирлиги)
# ===============================

class Unit(models.Model):
    name = models.CharField("Номи", max_length=50)
    short_name = models.CharField("Қисқартма", max_length=20)

    class Meta:
        verbose_name = "Ўлчов бирлиги"
        verbose_name_plural = "Ўлчов бирликлари"

    def __str__(self):
        return self.short_name


# ===============================
# PRODUCT (Маҳсулот / Товар)
# ===============================

class Product(models.Model):
    name = models.CharField("Маҳсулот номи", max_length=255)
    unit = models.ForeignKey(Unit,on_delete=models.PROTECT,verbose_name="Ўлчов бирлиги")
    is_active = models.BooleanField("Фаол", default=True)

    class Meta:
        verbose_name = "Маҳсулот"
        verbose_name_plural = "Маҳсулотлар"

    def __str__(self):
        return self.name

# ===============================
# LOCATION
# ===============================

class Region(models.Model):
    name = models.CharField("Вилоят", max_length=200, unique=True)

    class Meta:
        verbose_name = "Вилоят"
        verbose_name_plural = "Вилоятлар"
        ordering = ["name"]

    def __str__(self):
        return self.name


class District(models.Model):
    region = models.ForeignKey(Region,on_delete=models.CASCADE,related_name="districts",verbose_name="Вилоят")
    name = models.CharField("Туман", max_length=200)

    class Meta:
        verbose_name = "Туман"
        verbose_name_plural = "Туманлар"
        unique_together = ("region", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.region.name})"


class Massive(models.Model):
    district = models.ForeignKey(District,on_delete=models.CASCADE,related_name="massives",verbose_name="Туман")
    name = models.CharField("Массив", max_length=200)

    class Meta:
        verbose_name = "Массив"
        verbose_name_plural = "Массивлар"
        unique_together = ("district", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.district.name})"
