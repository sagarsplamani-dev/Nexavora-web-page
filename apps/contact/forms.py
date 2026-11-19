import uuid

from django import forms

from .models import Enquiry


class EnquiryForm(forms.ModelForm):
    submission_key = forms.UUIDField(
        initial=uuid.uuid4,
        widget=forms.HiddenInput,
    )
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "tabindex": "-1",
                "aria-hidden": "true",
                "class": "visually-hidden",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("website"):
            raise forms.ValidationError("Unable to accept this submission.")
        return cleaned_data


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()


class CallbackForm(EnquiryForm):
    course = forms.ChoiceField(
        required=True,
        label="Interested Program / Course",
        choices=[
            ("", "Course / curriculum details"),
            ("Data Science", "Data Science"),
            ("Data Analytics", "Data Analytics"),
        ],
    )
    phone = forms.RegexField(
        regex=r"^\d{10}$",
        max_length=10,
        label="Mobile Number",
        error_messages={"invalid": "Enter a 10-digit mobile number."},
        widget=forms.TextInput(
            attrs={
                "type": "tel",
                "inputmode": "numeric",
                "autocomplete": "tel-national",
                "pattern": "[0-9]{10}",
                "placeholder": "10-digit mobile number",
            }
        ),
    )

    class Meta:
        model = Enquiry
        fields = ["name", "email", "phone", "course", "message"]
        labels = {"email": "Email Address"}
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Your name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "Your email address"}),
            "message": forms.Textarea(
                attrs={"placeholder": "What would you like to learn about?", "rows": 3}
            ),
        }


class ContactForm(EnquiryForm):
    class Meta:
        model = Enquiry
        fields = ["name", "email", "subject", "phone", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Your name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "Email address"}),
            "subject": forms.TextInput(attrs={"placeholder": "Subject"}),
            "phone": forms.TextInput(attrs={"type": "tel", "autocomplete": "tel", "placeholder": "Phone (optional)"}),
            "message": forms.Textarea(attrs={"placeholder": "Message", "rows": 3}),
        }
