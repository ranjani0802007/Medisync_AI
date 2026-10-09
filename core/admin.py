from django.contrib import admin
from .models import Case, Doctor, KV

admin.site.register(Doctor)
admin.site.register(Case)
admin.site.register(KV)
