from django.contrib import admin
from .models import Login, CompanyDetails, Return, Score, CompanyGSTRecord

@admin.register(Login)
class LoginAdmin(admin.ModelAdmin):
    list_display = ('id', 'username')  # Display the ID and user fields in the admin list view

@admin.register(CompanyDetails)
class CompanyDetailsAdmin(admin.ModelAdmin):
    list_display = ('gstin', 'legal_name', 'trade_name', 'status')  # Customize fields to display
    search_fields = ('gstin', 'legal_name')  # Add search functionality
    list_filter = ('status', 'entity_type')  # Add filter options

@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('company', 'return_type', 'date_of_filing', 'status')
    search_fields = ('arn',)
    list_filter = ('return_type', 'status')

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('company', 'delayed_filing', 'average_delay_days')

@admin.register(CompanyGSTRecord)
class CompanyGSTRecordAdmin(admin.ModelAdmin):
    list_display = ('gstin', 'legal_name', 'city', 'state')
    search_fields = ('gstin', 'legal_name')
    list_filter = ('state',)
