from rest_framework import serializers
from .models import Inventory

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['name','category','price','quantity','barcode','description','supplier']
    
    def create(self, validated_data):
        request = self.context.get("request")
        validated_data['created_by'] = request.user
        return super().create(validated_data)
