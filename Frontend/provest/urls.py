from django.urls import path
from provest import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_request, name="login"),
    path("logout/", views.logout_request, name="logout"),
    path("provest/propertysearch/", views.search, name="search"),
    path("provest/propertysearch/display/", views.searchdisplay, name="searchdisplay"),
    path("provest/propertysearch/display/<p_id>", views.propdetails, name="propdetails"),
    path("provest/propertysearch/display/<p_id>/graph", views.prop_graph, name="propgraph"),
    path("provest/savedproperties/", views.savedproperties, name="savedproperties"),
]