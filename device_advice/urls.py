from django.urls import path

from . import views
from . import schema

urlpatterns = [
    path('', views.index, name='index'),
    #path("graphql", views.GraphQLView.as_view(graphiql=True, schema=schema)),
]
