from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import LoginView, CompanyViewSet, CompanyDetailView
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
# router.register(r'login', views.LoginViewSet, basename='login')
router.register(r'companies', views.CompanyViewSet)
router.register(r'returns', views.ReturnViewSet)
router.register(r'scores', views.ScoreViewSet)



urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('companies/<str:gstin>/', CompanyDetailView.as_view(), name='company-detail'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('update_gst_record/', views.update_gst_record, name='update_gst_record'),
    path('fetch_and_save_gst_record/', views.fetch_and_save_gst_record, name='fetch_and_save_gst_record'),
    path('', include(router.urls)), 
]



            
