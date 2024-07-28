from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from .serializers import ItemSerializer



@login_required(login_url='login')
def userItems(request):
    """"""