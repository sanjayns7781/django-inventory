from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import PostSerializer, GetSerializer, PutSerializer, BulkSerializer, InventoryQuantityUpdateModelSerializer, InventoryImportSerializer
from rest_framework.response import Response
from rest_framework import status
from .models import Inventory
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import permission_classes
from .permissions import IsAdmin,IsAdminOrManager
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count,Sum,F
from django.http import Http404, HttpResponse, JsonResponse
import csv,io,json

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

# Task 8: Advanced Inventory Queries
# Endpoint:GET /api/inventory/categories/
# Endpoint:GET /api/inventory/low-stock/
class GetBYCategories(APIView):
    def get(self,request):
        categories =(
            Inventory.objects
            .filter(is_active=True) # optional remove if want inactive items also
            .values('category')
            .annotate(count=Count('id'))
            .order_by('category') 
        )

        return Response(categories, status=status.HTTP_200_OK)
    
class GetLowStock(APIView):
    def get(self,request):
        permission_classes = [IsAdminOrManager,IsAuthenticated]
        threshold = request.query_params.get("threshold")
        if threshold:
            items = Inventory.objects.filter(quantity__lte=threshold)
        else:
            items = Inventory.objects.filter(quantity__lte=5)

        serializer = GetSerializer(items,many=True)
        return Response(serializer.data,status=200)
    
# GET /api/inventory/by-supplier/{supplier}/ 
class GetBySupplier(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,supplier):
        items = Inventory.objects.filter(supplier=supplier)
        if not items.exists():
            raise Http404("No suppliers found")
        serializer = GetSerializer(items,many=True)
        return Response(serializer.data,status=200)
    
# Task 9: Inventory Statistics (Admin/Manager Only)
# remaining 10,12,9

class GetStatistics(APIView):
    permission_classes = [IsAuthenticated,IsAdminOrManager]
    def get(self,request):
        total_items = Inventory.objects.count()
        total_categories = Inventory.objects.values('category').distinct().count()
        total_value = Inventory.objects.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
        low_stock_items = Inventory.objects.filter(quantity__lte=5, quantity__gt=0).count()
        out_of_stock_items = Inventory.objects.filter(quantity=0).count()
        top_categories = (
            Inventory.objects
            .values('category')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        data = {
            "total_items": total_items,
            "total_categories": total_categories,
            "total_value": total_value,
            "low_stock_items": low_stock_items,
            "out_of_stock_items": out_of_stock_items,
            "top_categories": top_categories,
        }
        return Response(data,status=200)

class BulkOperations(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        serializer = BulkSerializer(data=request.data,many=True,context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        serializer = InventoryQuantityUpdateModelSerializer(
            data=request.data.get('updates'), many=True
        )
        serializer.is_valid(raise_exception=True)

        updated_items = serializer.update_bulk()

        # Serialize the updated objects for response
        response_serializer = InventoryQuantityUpdateModelSerializer(updated_items, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

#  Export & Import (Admin/Manager Only) 
#   
class Analytics(APIView):
    def get(self,request):
        export_format = request.query_params.get('format', 'json').lower()
        queryset = Inventory.objects.all()
        serializer = GetSerializer(queryset, many=True)

        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="inventory.csv"'

            writer = csv.writer(response)
            writer.writerow(serializer.data[0].keys() if serializer.data else [])
            for item in serializer.data:
                writer.writerow(item.values())
            return response
        return JsonResponse(serializer.data, safe=False, status=200)

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        decoded_file = file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        items = list(reader)
        serializer = InventoryImportSerializer(data=items, many=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




