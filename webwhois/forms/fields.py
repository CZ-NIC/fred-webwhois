from django import forms


class RemoveWhitespacesField(forms.CharField):
    """Remove white spaces from the beginning and end of the value."""

    def to_python(self, value):
        if value is not None:
            value = value.strip()
        return value
