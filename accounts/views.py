from django.shortcuts import render
import requests
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView
from .serializers import RegisterSerializer, LoginSerializer, ProfileSerializer, GeminiChatSerializer, UpdateProfileSerializer
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit # type: ignore
import logging
from rest_framework.permissions import AllowAny
from django.conf import settings
from .models import Role,User
from .permissions import IsAdmin, IsAdminOrManager, IsCustomer
from django.db.models import Q
from google import genai
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView # pyright: ignore[reportMissingImports]

logger = logging.getLogger(__name__)

# Create your views here.
class RegisterView(APIView):

    @ratelimit(key='ip', rate='5/m', block=True) 
    def post(self,request):
        # Check if the request was blocked by rate limiting
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for IP: {self.get_client_ip(request)}")
            return Response(
                {"detail": "Too many requests. Try again later."}, 
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = RegisterSerializer(data=request.data,context = {"request":request})
        if serializer.is_valid():
            # logger.info(f"User {serializer.validated_data['username']} logged in successfully")
            serializer.save()
            return Response(serializer.data,status=201)
        return Response(serializer.errors,status=400)

@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        # Check if rate limit triggered
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for IP: {self.get_client_ip(request)}")
            return Response(
                {"detail": "Too many requests. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.warning(f"Failed login attempt for username: {request.data.get('username')}")
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.user
        logger.info(f"User {user.username} logged in successfully")

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    def get_client_ip(self, request):
        """Helper to fetch client IP for logging"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

# Task 4: User Profile Management
# GET /api/users/profile/
# PUT /api/users/profile/
class ProfileManagementView(APIView):
    def get(self,request):
        user = User.objects.select_related('role').get(id=request.user.id)
        serializer = ProfileSerializer(user)
        return Response(serializer.data,status=201)
    
    def put(self,request):
        user = User.objects.get(id=request.user.id)
        serializer = UpdateProfileSerializer(instance=user,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Details has been succesfully updated by {request.user.username}")
            return Response(serializer.data,status=200)
        return Response(serializer.errors,status=400)

# Task 5: User Management (Admin/Manager Only)
# GET /api/users/
class AllProfileManagemenetView(APIView):
    @permission_classes([IsAdminOrManager])
    def get(self,request,id=None):
        if not id:
            users = User.objects.select_related('role').all()

            role = request.query_params.get('role',None)
            if role:
                users =users.filter(role=role)

            is_active = request.query_params.get('is_active')
            if is_active is not None:
                users = users.filter(is_active=is_active.lower() in ['true', '1'])

            search = request.query_params.get("search"  )
            if search:
                users = users.filter(
                    Q(username__icontains=search)|
                    Q(email__icontains=search)|
                    Q(first_name__icontains=search)|
                    Q(last_name__icontains=search)
                )
            serializer = ProfileSerializer(users,many=True)
            return Response(serializer.data,status=201)
        
        else:
            user = get_object_or_404(User.objects.select_related("role"), id=id)
            serializer = ProfileSerializer(instance=user)
            return Response(serializer.data,status=201)
    
    @permission_classes([IsAdminOrManager])
    def put(self,request,id):
        user = get_object_or_404(User.objects.select_related('role', id=id))
        serializer = UpdateProfileSerializer(instance=user,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=200)
        return Response(serializer.errors,status=400)
    
    def delete(self,request,id):
        user = User.objects.filter(id=id).first()
        if user:
            user.is_active=False
            user.save()
            return Response(status=204)
        else:
            return Response({"detail": "There is no user with given id"},status=400)

class GeminiChatView(APIView):
    """
    Accepts user message and returns a response from Google Gemini API.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GeminiChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.validated_data['message']

        # Initialize Gemini client
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        try:
            # Call Gemini model
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # or choose the model you want
                contents=user_message
            )

            reply = response.text  # Gemini response text
            logger.info(f"User {request.user} sent message. Gemini replied successfully.")

            return Response({"reply": reply}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return Response(
                {"error": "Failed to get response from Gemini."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )