from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q, RestrictedError, Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import generic

from wm_light.forms import (
    ItemCategoryForm,
    SearchForm,
    StockItemForm,
    StockMovementForm,
    UnitOfMeasureForm,
    WarehouseClerkCreationForm,
    WarehouseClerkUpdateForm,
    WarehouseForm,
)
from wm_light.models import (
    ItemCategory,
    StockBalance,
    StockItem,
    StockMovement,
    UnitOfMeasure,
    Warehouse,
    WarehouseClerk,
)


@login_required
def index(request):
    context = {
        "num_clerks": WarehouseClerk.objects.count(),
        "num_units": UnitOfMeasure.objects.count(),
        "num_categories": ItemCategory.objects.count(),
        "num_items": StockItem.objects.count(),
        "num_warehouses": Warehouse.objects.count(),
        "num_movements": StockMovement.objects.count(),
        "total_quantity": StockBalance.objects.aggregate(
            total=Sum("quantity")
        )["total"] or 0,
        "last_movements": StockMovement.objects.select_related(
            "stock_item", "warehouse"
        )[:5],
    }
    return render(request, "index.html", context)


class BaseListView(LoginRequiredMixin, generic.ListView):
    """Generic list: search by `search_fields`, pagination, table columns."""

    template_name = "list.html"
    paginate_by = 10
    title = ""
    columns = []
    search_fields = ("name",)
    # URL names; None hides the corresponding button
    create_url = None
    update_url = None
    delete_url = None

    def get_queryset(self):
        queryset = super().get_queryset()
        form = SearchForm(self.request.GET)
        if form.is_valid() and form.cleaned_data["q"]:
            query = Q()
            for field in self.search_fields:
                query |= Q(**{f"{field}__icontains": form.cleaned_data["q"]})
            queryset = queryset.filter(query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context.update(
            {
                "title": self.title,
                "columns": self.columns,
                "search_form": SearchForm(self.request.GET),
                "create_url": self.create_url,
                "update_url": self.update_url,
                "delete_url": self.delete_url,
                "query": urlencode(params),
            }
        )
        return context


class BaseFormViewMixin(LoginRequiredMixin):
    template_name = "form.html"
    title = ""
    success_url = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.title
        context["cancel_url"] = self.success_url
        return context


class BaseDeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = "confirm_delete.html"
    title = ""
    success_url = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.title
        context["cancel_url"] = self.success_url
        return context

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except RestrictedError:
            messages.error(
                self.request,
                "Cannot delete this record: it is used by other records.",
            )
        except ValidationError as error:
            messages.error(self.request, " ".join(error.messages))
        return redirect(self.success_url)


class WarehouseClerkListView(BaseListView):
    model = WarehouseClerk
    title = "Warehouse clerks"
    columns = [
        ("Username", "username"),
        ("First name", "first_name"),
        ("Last name", "last_name"),
        ("Email", "email"),
        ("Phone", "phone_number"),
    ]
    search_fields = ("username", "first_name", "last_name", "email")
    create_url = "wm_light:clerk-create"
    update_url = "wm_light:clerk-update"
    delete_url = "wm_light:clerk-delete"


class WarehouseClerkCreateView(BaseFormViewMixin, generic.CreateView):
    model = WarehouseClerk
    form_class = WarehouseClerkCreationForm
    title = "New warehouse clerk"
    success_url = reverse_lazy("wm_light:clerk-list")


class WarehouseClerkUpdateView(BaseFormViewMixin, generic.UpdateView):
    model = WarehouseClerk
    form_class = WarehouseClerkUpdateForm
    title = "Edit warehouse clerk"
    success_url = reverse_lazy("wm_light:clerk-list")


class WarehouseClerkDeleteView(BaseDeleteView):
    model = WarehouseClerk
    title = "Delete warehouse clerk"
    success_url = reverse_lazy("wm_light:clerk-list")


class UnitOfMeasureListView(BaseListView):
    model = UnitOfMeasure
    title = "Units of measure"
    columns = [("Name", "name"), ("Full name", "full_name")]
    search_fields = ("name", "full_name")
    create_url = "wm_light:unit-create"
    update_url = "wm_light:unit-update"
    delete_url = "wm_light:unit-delete"


class UnitOfMeasureCreateView(BaseFormViewMixin, generic.CreateView):
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    title = "New unit of measure"
    success_url = reverse_lazy("wm_light:unit-list")


class UnitOfMeasureUpdateView(BaseFormViewMixin, generic.UpdateView):
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    title = "Edit unit of measure"
    success_url = reverse_lazy("wm_light:unit-list")


class UnitOfMeasureDeleteView(BaseDeleteView):
    model = UnitOfMeasure
    title = "Delete unit of measure"
    success_url = reverse_lazy("wm_light:unit-list")


class ItemCategoryListView(BaseListView):
    model = ItemCategory
    title = "Item categories"
    columns = [("Name", "name")]
    create_url = "wm_light:category-create"
    update_url = "wm_light:category-update"
    delete_url = "wm_light:category-delete"


class ItemCategoryCreateView(BaseFormViewMixin, generic.CreateView):
    model = ItemCategory
    form_class = ItemCategoryForm
    title = "New item category"
    success_url = reverse_lazy("wm_light:category-list")


class ItemCategoryUpdateView(BaseFormViewMixin, generic.UpdateView):
    model = ItemCategory
    form_class = ItemCategoryForm
    title = "Edit item category"
    success_url = reverse_lazy("wm_light:category-list")


class ItemCategoryDeleteView(BaseDeleteView):
    model = ItemCategory
    title = "Delete item category"
    success_url = reverse_lazy("wm_light:category-list")


class StockItemListView(BaseListView):
    model = StockItem
    queryset = (
        StockItem.objects.select_related("unit_of_measure").prefetch_related(
            "categories"
        )
    )
    title = "Stock items"
    columns = [
        ("Name", "name"),
        ("Unit", "unit_of_measure.name"),
        ("Categories", "get_categories_display"),
    ]
    search_fields = ("name", "categories__name")
    create_url = "wm_light:item-create"
    update_url = "wm_light:item-update"
    delete_url = "wm_light:item-delete"

    def get_queryset(self):
        # categories__name search can duplicate rows
        return super().get_queryset().distinct()


class StockItemCreateView(BaseFormViewMixin, generic.CreateView):
    model = StockItem
    form_class = StockItemForm
    title = "New stock item"
    success_url = reverse_lazy("wm_light:item-list")


class StockItemUpdateView(BaseFormViewMixin, generic.UpdateView):
    model = StockItem
    form_class = StockItemForm
    title = "Edit stock item"
    success_url = reverse_lazy("wm_light:item-list")


class StockItemDeleteView(BaseDeleteView):
    model = StockItem
    title = "Delete stock item"
    success_url = reverse_lazy("wm_light:item-list")


class WarehouseListView(BaseListView):
    model = Warehouse
    queryset = Warehouse.objects.select_related("warehouse_clerk")
    title = "Warehouses"
    columns = [("Name", "name"), ("Clerk", "warehouse_clerk")]
    search_fields = ("name", "warehouse_clerk__username")
    create_url = "wm_light:warehouse-create"
    update_url = "wm_light:warehouse-update"
    delete_url = "wm_light:warehouse-delete"


class WarehouseCreateView(BaseFormViewMixin, generic.CreateView):
    model = Warehouse
    form_class = WarehouseForm
    title = "New warehouse"
    success_url = reverse_lazy("wm_light:warehouse-list")


class WarehouseUpdateView(BaseFormViewMixin, generic.UpdateView):
    model = Warehouse
    form_class = WarehouseForm
    title = "Edit warehouse"
    success_url = reverse_lazy("wm_light:warehouse-list")


class WarehouseDeleteView(BaseDeleteView):
    model = Warehouse
    title = "Delete warehouse"
    success_url = reverse_lazy("wm_light:warehouse-list")


class StockBalanceListView(BaseListView):
    model = StockBalance
    queryset = StockBalance.objects.select_related(
        "stock_item__unit_of_measure", "warehouse"
    )
    title = "Stock balances"
    columns = [
        ("Warehouse", "warehouse.name"),
        ("Stock item", "stock_item.name"),
        ("Quantity", "quantity"),
        ("Unit", "stock_item.unit_of_measure.name"),
    ]
    search_fields = ("stock_item__name", "warehouse__name")


class StockMovementListView(BaseListView):
    model = StockMovement
    queryset = StockMovement.objects.select_related(
        "stock_item__unit_of_measure", "warehouse"
    )
    title = "Stock movements"
    columns = [
        ("Date", "movement_date"),
        ("Type", "movement_type"),
        ("Warehouse", "warehouse.name"),
        ("Stock item", "stock_item.name"),
        ("Quantity", "quantity"),
        ("Balance change", "quantity_for_balance"),
    ]
    search_fields = ("stock_item__name", "warehouse__name")
    create_url = "wm_light:movement-create"
    update_url = "wm_light:movement-update"
    delete_url = "wm_light:movement-delete"


class StockMovementFormMixin(BaseFormViewMixin):
    model = StockMovement
    form_class = StockMovementForm
    success_url = reverse_lazy("wm_light:movement-list")

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)


class StockMovementCreateView(StockMovementFormMixin, generic.CreateView):
    title = "New stock movement"


class StockMovementUpdateView(StockMovementFormMixin, generic.UpdateView):
    title = "Edit stock movement"


class StockMovementDeleteView(BaseDeleteView):
    model = StockMovement
    title = "Delete stock movement"
    success_url = reverse_lazy("wm_light:movement-list")
