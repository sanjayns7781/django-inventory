from django.shortcuts import render
from rest_framework.views import APIView
from serializers import RegisterSerializer,LoginSerializer
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit  # type: ignore
import logging
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