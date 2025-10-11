from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import PostSerializer, GetSerializer, PutSerializer
from rest_framework.response import Response
from rest_framework import status
from .models import Inventory
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import permission_classes
from .permissions import IsAdmin,IsAdminOrManager
from rest_framework.permissions import IsAuthenticated
# Create your views here.
# Task 7: Inventory CRUD Operations
# POST /api/inventory/
# GET /api/inventory/
class InventoryManagement(APIView):
    def post(self,request):
        serializer = PostSerializer(data=request.data,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=201)
        return Response(serializer.errors,status=400)
    
    def get(self,request):
        InventoryItems = Inventory.objects.select_related('created_by').all()

        category = request.query_params.get("category")
        if category:
            InventoryItems = InventoryItems.filter(category=category)

        min_price = request.query_params.get("min_price")
        if min_price:
            InventoryItems = InventoryItems.filter(price__gte=min_price)

        max_price = request.query_params.get("max_price")
        if max_price:
            InventoryItems = InventoryItems.filter(price__lte=max_price)


        in_stock = request.query_params.get("in_stock")
        if in_stock:
            InventoryItems = InventoryItems.filter(quantity__gte=1)

        created_by = request.query_params.get("created_by")
        if created_by.upper() in ['ADMIN', 'MANAGER']:
            InventoryItems = InventoryItems.filter(created_by__role_name=created_by.upper())
        
        search = request.query_params.get("search")
        if search:
            InventoryItems = InventoryItems.filter(
                Q(name__icontains = search)|
                Q(description__icontains= search)|
                Q(supplier__icontains = search)
            )

        ordering = request.query_params.get("ordering")
        if ordering:
            InventoryItems = InventoryItems.order_by(ordering)

        serializer = GetSerializer(InventoryItems, many=True)
        return Response(serializer.data)
    
class InventoryManagementWithId(APIView):
    def get(self,request,id):
        InventoryItem = get_object_or_404(Inventory,id=id)
        serializer = GetSerializer(instance=InventoryItem)
        return Response(serializer.data,status=200)
        

    def put(self,request,id):
        InventoryItem = get_object_or_404(Inventory,id=id)

        serializer = PutSerializer(
            instance=InventoryItem,
            data=request.data,
            context={"request":request},
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=200)
        return Response(serializer.errors,status=400)
        
    @permission_classes([IsAuthenticated])
    def delete(self,request,id):
        InventoryItem = get_object_or_404(Inventory,id=id)
        if request.user == InventoryItem.created_by or request.user.role_name in ["ADMIN", "MANAGER"]:
            InventoryItem.is_active=False
            InventoryItem.save()
            return Response({"detail": "Successfully soft deleted"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "You do not have permission to delete this item."},status=status.HTTP_403_FORBIDDEN)

        