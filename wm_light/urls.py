from django.urls import path

from wm_light import views

urlpatterns = [
    path("", views.index, name="index"),
    # Warehouse clerks
    path("clerks/", views.WarehouseClerkListView.as_view(), name="clerk-list"),
    path("clerks/create/", views.WarehouseClerkCreateView.as_view(), name="clerk-create"),
    path("clerks/<int:pk>/update/", views.WarehouseClerkUpdateView.as_view(), name="clerk-update"),
    path("clerks/<int:pk>/delete/", views.WarehouseClerkDeleteView.as_view(), name="clerk-delete"),
    # Units of measure
    path("units/", views.UnitOfMeasureListView.as_view(), name="unit-list"),
    path("units/create/", views.UnitOfMeasureCreateView.as_view(), name="unit-create"),
    path("units/<int:pk>/update/", views.UnitOfMeasureUpdateView.as_view(), name="unit-update"),
    path("units/<int:pk>/delete/", views.UnitOfMeasureDeleteView.as_view(), name="unit-delete"),
    # Item categories
    path("categories/", views.ItemCategoryListView.as_view(), name="category-list"),
    path("categories/create/", views.ItemCategoryCreateView.as_view(), name="category-create"),
    path("categories/<int:pk>/update/", views.ItemCategoryUpdateView.as_view(), name="category-update"),
    path("categories/<int:pk>/delete/", views.ItemCategoryDeleteView.as_view(), name="category-delete"),
    # Stock items
    path("items/", views.StockItemListView.as_view(), name="item-list"),
    path("items/create/", views.StockItemCreateView.as_view(), name="item-create"),
    path("items/<int:pk>/update/", views.StockItemUpdateView.as_view(), name="item-update"),
    path("items/<int:pk>/delete/", views.StockItemDeleteView.as_view(), name="item-delete"),
    # Warehouses
    path("warehouses/", views.WarehouseListView.as_view(), name="warehouse-list"),
    path("warehouses/create/", views.WarehouseCreateView.as_view(), name="warehouse-create"),
    path("warehouses/<int:pk>/update/", views.WarehouseUpdateView.as_view(), name="warehouse-update"),
    path("warehouses/<int:pk>/delete/", views.WarehouseDeleteView.as_view(), name="warehouse-delete"),
    # Stock balances (read only)
    path("balances/", views.StockBalanceListView.as_view(), name="balance-list"),
    # Stock movements
    path("movements/", views.StockMovementListView.as_view(), name="movement-list"),
    path("movements/create/", views.StockMovementCreateView.as_view(), name="movement-create"),
    path("movements/<int:pk>/update/", views.StockMovementUpdateView.as_view(), name="movement-update"),
    path("movements/<int:pk>/delete/", views.StockMovementDeleteView.as_view(), name="movement-delete"),
]

app_name = "wm_light"
