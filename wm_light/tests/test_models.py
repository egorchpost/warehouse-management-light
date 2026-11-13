from django.test import TestCase
from django.core.exceptions import ValidationError

from wm_light.models import (
    WarehouseClerk,
    UnitOfMeasure,
    ItemCategory,
    StockItem,
    Warehouse,
    StockBalance,
    StockMovement,
    DirectBalanceChangeError,
)


class StockMovementTests(TestCase):

    def setUp(self):
        """Create common test objects."""

        self.clerk = WarehouseClerk.objects.create_user(
            username="test_clerk",
            password="test123",
        )

        self.unit = UnitOfMeasure.objects.create(
            name="kg",
            full_name="Kilogram",
        )

        self.category = ItemCategory.objects.create(
            name="Food",
        )

        self.item = StockItem.objects.create(
            name="Sugar",
            unit_of_measure=self.unit,
        )
        self.item.categories.add(self.category)

        self.warehouse = Warehouse.objects.create(
            name="Main warehouse",
            warehouse_clerk=self.clerk,
        )

    def create_movement(self, movement_type, quantity):
        """Helper method for creating stock movements."""

        return StockMovement.objects.create(
            stock_item_id=self.item.id,
            warehouse_id=self.warehouse.id,
            movement_type=movement_type,
            quantity=quantity,
        )

    def get_balance(self):
        return StockBalance.objects.get(
            stock_item=self.item,
            warehouse=self.warehouse,
        )

    # ---------- CREATE ----------

    def test_create_in_movement(self):
        """IN movement increases stock balance."""

        movement = self.create_movement(
            StockMovement.IN,
            100,
        )

        self.assertEqual(movement.quantity_for_balance, 100)
        self.assertEqual(self.get_balance().quantity, 100)

    def test_create_out_movement(self):
        """OUT movement decreases stock balance."""

        self.create_movement(StockMovement.IN, 100)

        movement = self.create_movement(
            StockMovement.OUT,
            30,
        )

        self.assertEqual(movement.quantity_for_balance, -30)
        self.assertEqual(self.get_balance().quantity, 70)

    def test_multiple_movements_update_same_balance(self):
        """Multiple movements update one balance."""

        self.create_movement(StockMovement.IN, 100)
        self.create_movement(StockMovement.OUT, 30)
        self.create_movement(StockMovement.IN, 20)

        self.assertEqual(self.get_balance().quantity, 90)

        self.assertEqual(
            StockBalance.objects.count(),
            1,
        )

    def test_quantity_for_balance_is_calculated_automatically(self):
        """Manually supplied quantity_for_balance is ignored."""

        movement = StockMovement(
            stock_item=self.item,
            warehouse=self.warehouse,
            movement_type=StockMovement.IN,
            quantity=50,
            quantity_for_balance=-999,
        )

        movement.save()

        self.assertEqual(movement.quantity_for_balance, 50)
        self.assertEqual(self.get_balance().quantity, 50)

    # ---------- UPDATE ----------

    def test_update_movement_quantity(self):
        """Updating movement quantity recalculates balance."""

        movement = self.create_movement(
            StockMovement.IN,
            100,
        )

        movement.quantity = 70
        movement.save()

        movement.refresh_from_db()

        self.assertEqual(movement.quantity_for_balance, 70)
        self.assertEqual(self.get_balance().quantity, 70)

    def test_update_movement_type(self):
        """Changing IN to OUT reverses previous movement."""

        movement = self.create_movement(
            StockMovement.IN,
            100,
        )

        movement.movement_type = StockMovement.OUT
        movement.quantity = 40
        movement.save()

        movement.refresh_from_db()

        self.assertEqual(movement.quantity_for_balance, -40)
        self.assertEqual(self.get_balance().quantity, -40)

    def test_update_movement_stock_item(self):
        """Changing stock item updates both balances."""

        self.create_movement(StockMovement.IN, 100)

        new_item = StockItem.objects.create(
            name="Flour",
            unit_of_measure=self.unit,
        )

        movement = StockMovement.objects.get(
            stock_item=self.item,
        )

        movement.stock_item = new_item
        movement.save()

        self.assertEqual(
            StockBalance.objects.get(stock_item=self.item).quantity,
            0,
        )

        self.assertEqual(
            StockBalance.objects.get(stock_item=new_item).quantity,
            100,
        )

    # ---------- DELETE ----------

    def test_delete_movement(self):
        """Deleting movement reverses its effect on balance."""

        movement = self.create_movement(
            StockMovement.IN,
            100,
        )

        movement.delete()

        self.assertEqual(self.get_balance().quantity, 0)

    def test_delete_out_movement(self):
        """Deleting OUT movement restores stock balance."""

        self.create_movement(StockMovement.IN, 100)

        movement = self.create_movement(
            StockMovement.OUT,
            30,
        )

        movement.delete()

        self.assertEqual(self.get_balance().quantity, 100)

    # ---------- VALIDATION ----------

    def test_quantity_must_be_positive(self):
        """Movement quantity cannot be zero or negative."""

        for quantity in (0, -10):
            with self.subTest(quantity=quantity):
                movement = StockMovement(
                    stock_item=self.item,
                    warehouse=self.warehouse,
                    movement_type=StockMovement.IN,
                    quantity=quantity,
                )

                with self.assertRaises(ValidationError):
                    movement.save()

    def test_invalid_movement_type(self):
        """Invalid movement type is rejected."""

        movement = StockMovement(
            stock_item=self.item,
            warehouse=self.warehouse,
            movement_type="INVALID",
            quantity=10,
        )

        with self.assertRaises(ValidationError):
            movement.save()


class StockBalanceProtectionTests(TestCase):

    def setUp(self):
        self.clerk = WarehouseClerk.objects.create_user(
            username="test_clerk",
            password="test123",
        )

        self.unit = UnitOfMeasure.objects.create(
            name="kg",
            full_name="Kilogram",
        )

        self.item = StockItem.objects.create(
            name="Sugar",
            unit_of_measure=self.unit,
        )

        self.warehouse = Warehouse.objects.create(
            name="Main warehouse",
            warehouse_clerk=self.clerk,
        )

        StockMovement.objects.create(
            stock_item=self.item,
            warehouse=self.warehouse,
            movement_type=StockMovement.IN,
            quantity=100,
        )

    def test_direct_stock_balance_creation_is_forbidden(self):
        """StockBalance cannot be created directly."""

        balance = StockBalance(
            stock_item=self.item,
            warehouse=self.warehouse,
            quantity=100,
        )

        with self.assertRaises(DirectBalanceChangeError):
            balance.save()

    def test_direct_stock_balance_update_is_forbidden(self):
        """StockBalance cannot be updated directly."""

        balance = StockBalance.objects.get(
            stock_item=self.item,
            warehouse=self.warehouse,
        )

        balance.quantity = 200

        with self.assertRaises(DirectBalanceChangeError):
            balance.save()

    def test_direct_stock_balance_delete_is_forbidden(self):
        """StockBalance cannot be deleted directly."""

        balance = StockBalance.objects.get(
            stock_item=self.item,
            warehouse=self.warehouse,
        )

        with self.assertRaises(DirectBalanceChangeError):
            balance.delete()
