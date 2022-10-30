from django.db import models

class Device(models.Model):
    name = models.CharField(max_length=200)
    wattage = models.IntegerField(default=0)
    def __str__(self):
        return self.name

class Task(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    use_case = models.CharField(max_length=200)
    duration = models.FloatField(default=0)
    def __str__(self):
        return self.use_case

