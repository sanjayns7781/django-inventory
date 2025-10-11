from rest_framework import serializers
from .models import Inventory
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

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
    
class BulkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['name','category','price','quantity','barcode','description','supplier']

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    

class InventoryQuantityUpdateModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['id', 'quantity']

    def update_bulk(self):
        """
        Custom method to update multiple inventory items.
        Expects validated_data as a list of dicts.
        """
        updated_items = []
        for item_data in self.validated_data:
            # Fetch the inventory item
            inventory_item = get_object_or_404(Inventory, id=item_data['id'])
            # Update quantity
            inventory_item.quantity = item_data['quantity']
            inventory_item.save()
            updated_items.append(inventory_item)
        return updated_items

class InventoryImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['name', 'category', 'price', 'quantity', 'barcode', 'description', 'supplier']

    def create(self, validated_data):
        # Set created_by from request
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)