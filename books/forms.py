from django import forms

class SubscriptionForm(forms.Form):
    PLAN_CHOICES = (
        ('monthly', 'Monthly - $9'),
        ('yearly', 'Yearly - $99'),
    )
    plan = forms.ChoiceField(choices=PLAN_CHOICES)
    promo_code = forms.CharField(max_length=20, required=False)
