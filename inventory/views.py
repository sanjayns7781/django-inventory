from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import PostSerializer
from rest_framework.response import Response

# Create your views here.
# Task 7: Inventory CRUD Operations
# POST /api/inventory/
class InventoryManagement(APIView):
    def post(self,request):
        serializer = PostSerializer(data=request.data,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=201)
        return Response(serializer.errors,status=400)