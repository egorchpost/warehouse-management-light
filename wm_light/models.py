from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import IntegrityError, transaction
from django.db import models
from django.utils import timezone


class DirectBalanceChangeError(Exception):
    """Raised on any attempt to write to StockBalance directly."""


class DirectMovementChangeError(Exception):
    """Raised on bulk operations that would bypass StockBalance updates."""


class ProtectedQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise DirectMovementChangeError(
            "Use StockMovement.save() instead."
        )

    def bulk_create(self, *args, **kwargs):
        raise DirectMovementChangeError(
            "Use StockMovement.save() instead."
        )

    def bulk_update(self, *args, **kwargs):
        raise DirectMovementChangeError(
            "Use StockMovement.save() instead."
        )

    def delete(self):
        raise DirectMovementChangeError(
            "Use StockMovement.delete() instead."
        )


class ProtectedManager(
    models.Manager.from_queryset(ProtectedQuerySet)
):
    pass


class WarehouseClerk(AbstractUser):
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["username"]

    def __str__(self):
        full_name = self.get_full_name()
        return f"{self.username} ({full_name})" if full_name else self.username


class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=20)
    full_name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]
        verbose_name = "unit of measure"
        verbose_name_plural = "units of measure"

    def __str__(self):
        return self.name


class ItemCategory(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]
        verbose_name = "item category"
        verbose_name_plural = "item categories"

    def __str__(self):
        return self.name


class StockItem(models.Model):
    name = models.CharField(max_length=200)
    unit_of_measure = (
        models.ForeignKey(UnitOfMeasure, on_delete=models.RESTRICT)
    )
    categories = (
        models.ManyToManyField(ItemCategory, related_name="stock_items")
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_categories_display(self):
        return ", ".join(category.name for category in self.categories.all())

    get_categories_display.short_description = "Categories"


class Warehouse(models.Model):
    name = models.CharField(max_length=200)
    warehouse_clerk = (
        models.ForeignKey(WarehouseClerk, on_delete=models.RESTRICT)
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class StockBalance(models.Model):
    stock_item = models.ForeignKey(StockItem, on_delete=models.RESTRICT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.RESTRICT)
    quantity = models.IntegerField()

    objects = ProtectedManager()

    class Meta:
        ordering = ["warehouse__name", "stock_item__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["stock_item", "warehouse"],
                name="unique_balance_per_item_and_warehouse",
            ),
        ]

    def __str__(self):
        return f"{self.stock_item} @ {self.warehouse}: {self.quantity}"

    def save(self, *args, **kwargs):
        if not getattr(self, "_allow_write", False):
            raise DirectBalanceChangeError(
                "StockBalance can only be changed through StockMovement."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise DirectBalanceChangeError(
            "StockBalance cannot be deleted directly."
        )


class StockMovement(models.Model):
    IN = "IN"
    OUT = "OUT"

    stock_item = models.ForeignKey(StockItem, on_delete=models.RESTRICT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.RESTRICT)
    movement_date = models.DateTimeField(default=timezone.now)
    movement_type = models.CharField(
        max_length=3,
        choices=[
            (IN, "IN"),
            (OUT, "OUT"),
        ],
    )
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    # Filled in automatically on save(): +quantity for IN, -quantity for OUT.
    quantity_for_balance = models.IntegerField(editable=False, default=0)

    objects = ProtectedManager()

    class Meta:
        ordering = ["-movement_date", "-id"]

    def __str__(self):
        return (
            f"{self.movement_type} {self.quantity} "
            f"{self.stock_item} @ {self.warehouse}"
        )

    def calculate_quantity_for_balance(self):
        if self.movement_type == self.IN:
            return self.quantity

        if self.movement_type == self.OUT:
            return -self.quantity

        raise ValidationError("Invalid movement type.")

    @staticmethod
    def change_stock_balance(stock_item_id, warehouse_id, delta):
        try:
            with transaction.atomic():
                balance = (
                    StockBalance.objects
                    .select_for_update()
                    .get(
                        stock_item_id=stock_item_id,
                        warehouse_id=warehouse_id,
                    )
                )

        except StockBalance.DoesNotExist:
            try:
                with transaction.atomic():
                    balance = StockBalance(
                        stock_item_id=stock_item_id,
                        warehouse_id=warehouse_id,
                        quantity=delta,
                    )
                    balance._allow_write = True
                    balance.save()
                    return

            except IntegrityError:
                pass

        with transaction.atomic():
            balance = (
                StockBalance.objects
                .select_for_update()
                .get(
                    stock_item_id=stock_item_id,
                    warehouse_id=warehouse_id,
                )
            )

            balance.quantity += delta
            balance._allow_write = True
            balance.save()

    def save(self, *args, **kwargs):
        with transaction.atomic():
            old = None

            if self.pk:
                old = (
                    StockMovement.objects
                    .select_for_update()
                    .filter(pk=self.pk)
                    .values(
                        "stock_item_id",
                        "warehouse_id",
                        "quantity_for_balance",
                    )
                    .first()
                )

            if self.quantity <= 0:
                raise ValidationError(
                    {"quantity": "Quantity must be positive."}
                )

            self.quantity_for_balance = (
                self.calculate_quantity_for_balance()
            )

            update_fields = kwargs.get("update_fields")

            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {
                    "quantity_for_balance"
                }

            super().save(*args, **kwargs)

            if old:
                self.change_stock_balance(
                    old["stock_item_id"],
                    old["warehouse_id"],
                    -old["quantity_for_balance"],
                )

            self.change_stock_balance(
                self.stock_item_id,
                self.warehouse_id,
                self.quantity_for_balance,
            )

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            movement = (
                StockMovement.objects
                .select_for_update()
                .get(pk=self.pk)
            )

            super().delete(*args, **kwargs)

            self.change_stock_balance(
                movement.stock_item_id,
                movement.warehouse_id,
                -movement.quantity_for_balance,
            )
