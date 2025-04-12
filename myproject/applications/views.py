from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from applications.models import Application
from applications.owners import OwnerListView, OwnerDetailView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
# Create your views here.
class ApplicationsListView(OwnerListView):
    model = Application
    template_name = "applications/application_list.html"

    def get(self, request) :
        strval =  request.GET.get("search", False)
        if strval :
            # Simple title-only search
            # __icontains for case-insensitive search
            query = Q(title__icontains=strval)
            query.add(Q(text__icontains=strval), Q.OR)
            query.add(Q(tags__name__in=[strval]), Q.OR)
            application_list = Application.objects.filter(query).select_related().distinct().order_by('-updated_at')[:10]
        else :
            application_list = Application.objects.all().order_by('-updated_at')[:10]
