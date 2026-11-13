from django import forms
from django.contrib.auth.forms import UserCreationForm

from wm_light.models import (
    ItemCategory,
    StockItem,
    StockMovement,
    UnitOfMeasure,
    Warehouse,
    WarehouseClerk,
)


class TablerFormMixin:
    """Adds Tabler CSS classes to all widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                continue
            elif isinstance(widget, forms.CheckboxInput):
                css = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = "form-select"
            else:
                css = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()


class SearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={"placeholder": "Search...", "class": "form-control"}
        ),
    )


class WarehouseClerkCreationForm(TablerFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = WarehouseClerk
        fields = UserCreationForm.Meta.fields + (
            "first_name",
            "last_name",
            "email",
            "phone_number",
        )


class WarehouseClerkUpdateForm(TablerFormMixin, forms.ModelForm):
    class Meta:
        model = WarehouseClerk
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "is_active",
        )


class UnitOfMeasureForm(TablerFormMixin, forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = "__all__"


class ItemCategoryForm(TablerFormMixin, forms.ModelForm):
    class Meta:
        model = ItemCategory
        fields = "__all__"


class StockItemForm(TablerFormMixin, forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=ItemCategory.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = StockItem
        fields = "__all__"


class WarehouseForm(TablerFormMixin, forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = "__all__"


class StockMovementForm(TablerFormMixin, forms.ModelForm):
    movement_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
    )

    class Meta:
        model = StockMovement
        fields = (
            "stock_item",
            "warehouse",
            "movement_date",
            "movement_type",
            "quantity",
        )
