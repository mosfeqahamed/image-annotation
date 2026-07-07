from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


def tokens_for_user(user):
    """Return a fresh access/refresh JWT pair for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Register a new user and return a JWT token pair."""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            **tokens_for_user(user),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticate a user with email + password, return a JWT token pair."""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Look up the user by email, then authenticate with their username.
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = authenticate(username=user_obj.username, password=password)
        if user is None:
            return Response(
                {'error': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response({
            **tokens_for_user(user),
            'user': UserSerializer(user).data,
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Blacklist the supplied refresh token so it can no longer be used."""
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response(
            {'error': 'A refresh token is required to log out.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        RefreshToken(refresh_token).blacklist()
    except Exception:
        return Response(
            {'error': 'Invalid or expired refresh token.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Return the current authenticated user's info."""
    return Response(UserSerializer(request.user).data)
