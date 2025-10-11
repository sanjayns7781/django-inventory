from rest_framework import serializers
from .models import Inventory
from rest_framework.exceptions import PermissionDenied
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['name','category','price','quantity','barcode','description','supplier']
    
    def create(self, validated_data):
        request = self.context.get("request")
        validated_data['created_by'] = request.user
        return super().create(validated_data)

class GetSerializer(serializers.ModelSerializer):
    """
    serializers.StringRelatedField() go to the str function of the foreign key field
    and return the string representation
    """
    created_by = serializers.StringRelatedField()
    class Meta:
        model = Inventory
        fields = '__all__'


class PutSerializer(serializers.ModelSerializer):
    """Serializer to handle the put operations"""

    class Meta:
        model = Inventory
        fields =['name','category','price','quantity','description']

    def update(self, instance, validated_data):
        request = self.context.get("request")
        current_user = request.user
        created_user = instance.created_by
        if current_user != created_user and current_user.role_name not in  ["ADMIN","MANAGER"]:
            raise PermissionDenied("You do not have permission to update this item.")
        return super().update(instance, validated_data)