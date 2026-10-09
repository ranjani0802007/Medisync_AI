from django.contrib.auth.models import User
from django.db import models


class Doctor(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=120, unique=True)
    specialization = models.CharField(max_length=80)
    experience = models.IntegerField(default=0)
    qualification = models.CharField(max_length=160, blank=True)
    council_no = models.CharField(max_length=40, blank=True)
    rating = models.CharField(max_length=8, default="New")
    review_count = models.IntegerField(default=0)
    tags = models.JSONField(default=list, blank=True)
    reviews = models.JSONField(default=list, blank=True)
    verified = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.specialization})"


class Case(models.Model):
    case_id = models.CharField(max_length=20, unique=True)
    owner = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, blank=True)
    risk = models.CharField(max_length=10, blank=True)
    pos = models.IntegerField(default=0)
    data = models.JSONField(default=dict)  # full de-identified case: labs, series, timeline, opinions
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.case_id


class KV(models.Model):
    """Privacy-check logs (PII detected, alerts) and the case counter."""
    key = models.CharField(max_length=40, unique=True)
    value = models.JSONField(default=list)

    def __str__(self):
        return self.key
