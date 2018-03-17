from django import forms
from .models import Customer, Products, ProductOrderHelper, ProductCounter, OrdersList


class FormProductCounter(forms.ModelForm):
    class Meta:
        model = ProductCounter
        fields = [
            'number_of_packages',
            'action',
            'owner'
        ]


class FormCustomer(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name',
            'phone',
            'email'
        ]

    def clean_email(self):
        print("in clean_email")
        email = self.cleaned_data.get('email')
        name = self.cleaned_data.get('name')
        if email and Customer.objects.filter(email=email).exclude(name=name).exists():
            print("in raise")
            raise forms.ValidationError(u'Customer exist, if you want to add another order for the same customer, use Find customer.')
        return email


class FormProductOrderHelper(forms.ModelForm):
    class Meta:
        model = ProductOrderHelper
        fields = [
            'product_id',
            'number_of_packages',
        ]


class FormProduct(forms.ModelForm):
    quantity = forms.IntegerField()

    class Meta:
        model = Products
        fields = [
            'product_name',
            'quantity',
        ]


class FormNote(forms.ModelForm):
    notes = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = OrdersList
        fields = [
            'notes',
        ]
