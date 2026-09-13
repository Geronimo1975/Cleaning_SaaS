"""Formularul de contact. Etichetele sunt copy public, deci în germană."""

from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(label="Name", max_length=120)
    email = forms.EmailField(label="E-Mail")
    subject = forms.CharField(label="Betreff", max_length=160)
    message = forms.CharField(label="Nachricht", widget=forms.Textarea, max_length=5000)
    privacy = forms.BooleanField(
        label="Ich habe die Datenschutzerklärung gelesen und stimme der Verarbeitung "
        "meiner Angaben zur Beantwortung der Anfrage zu."
    )
