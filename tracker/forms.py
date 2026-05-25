from django import forms

from .models import Dividend, DividendFrequency, Holding, Ticker


class TickerQuickAddForm(forms.Form):
    symbol = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "예: AAPL, KO, MSFT"}
        ),
    )

    def clean_symbol(self):
        return self.cleaned_data["symbol"].strip().upper()


class TickerForm(forms.ModelForm):
    class Meta:
        model = Ticker
        fields = ["symbol", "name", "currency", "dividend_frequency"]
        widgets = {
            "symbol": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "currency": forms.TextInput(attrs={"class": "form-control"}),
            "dividend_frequency": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_symbol(self):
        return self.cleaned_data["symbol"].strip().upper()


class HoldingForm(forms.ModelForm):
    class Meta:
        model = Holding
        fields = ["ticker", "shares", "average_cost", "acquired_at", "notes"]
        widgets = {
            "ticker": forms.Select(attrs={"class": "form-select"}),
            "shares": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
            "average_cost": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
            "acquired_at": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class DividendForm(forms.ModelForm):
    class Meta:
        model = Dividend
        fields = ["ticker", "ex_date", "pay_date", "amount_per_share", "source"]
        widgets = {
            "ticker": forms.Select(attrs={"class": "form-select"}),
            "ex_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "pay_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount_per_share": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
            "source": forms.Select(attrs={"class": "form-select"}),
        }
