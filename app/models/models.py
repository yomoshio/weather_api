
from tortoise import fields, models
from datetime import datetime


class SearchHistory(models.Model):
    id = fields.IntField(pk=True)
    user_id = fields.CharField(max_length=255, index=True)
    city = fields.CharField(max_length=100, index=True)
    temperature = fields.FloatField()
    timestamp = fields.DatetimeField(default=datetime.utcnow)
    
    class Meta:
        table = "search_history"
        ordering = ["-timestamp"]
    
    def __str__(self):
        return f"SearchHistory(city='{self.city}', temp={self.temperature})"