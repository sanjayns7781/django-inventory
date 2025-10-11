from django.urls import path
from .views import (
    InventoryManagement, InventoryManagementWithId, GetBYCategories,
    GetLowStock, GetBySupplier, GetStatistics, BulkOperations, Analytics

)

urlpatterns = [
    path('inventory/',InventoryManagement.as_view(),name="get_and_post"),
    path('inventory/<int:id>/',InventoryManagementWithId.as_view(),name="get_and_post_withid"),
    path('inventory/categories/',GetBYCategories.as_view()),
    path('inventory/low-stock/',GetLowStock.as_view()),
    path('inventory/by-supplier/<str:supplier>/',GetBySupplier.as_view()),
    path('inventory/stats/',GetStatistics.as_view()),
    path('inventory/bulk-create/',BulkOperations.as_view()),
    path('inventory/export/',Analytics.as_view()),
    path('inventory/import/',Analytics.as_view()),

]
