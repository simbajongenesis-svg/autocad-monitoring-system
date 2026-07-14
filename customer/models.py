from django.db import models
from django.contrib.auth.models import User

class Sender(models.Model):
    company_name = models.CharField(max_length=255)
    address = models.TextField()
    contact_number = models.CharField(max_length=100)

    def __str__(self):
        return self.company_name


class Customer(models.Model):
    fullname_or_companyname = models.CharField(max_length=255)
    care_of = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField()
    contact_number = models.CharField(max_length=100)
    notes_or_remarks = models.TextField(blank=True, null=True)

    sender = models.ForeignKey(Sender, on_delete=models.SET_NULL, null=True, blank=True)  # 👈 add sender

    def __str__(self):
        return self.fullname_or_companyname
