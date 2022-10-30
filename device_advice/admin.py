from django.contrib import admin

# Register your models here.
from .models import Device, Task

admin.site.register(Device)
admin.site.register(Task)
