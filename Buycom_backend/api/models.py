from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password


# Login Table
class Login(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.username
    
    # You should hash the password before saving it
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
# Company Details Table
class CompanyDetails(models.Model):
    gstin = models.CharField(max_length=15, unique=True)
    legal_name = models.CharField(max_length=255)
    trade_name = models.CharField(max_length=255)
    state_jurisdiction_code = models.CharField(max_length=10)
    state_jurisdiction = models.CharField(max_length=50)
    central_jurisdiction_code = models.CharField(max_length=10)
    central_jurisdiction = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    entity_type = models.CharField(max_length=50)
    business_nature = models.JSONField()  # Store as JSON
    principal_address = models.JSONField()
    registration_date = models.CharField(max_length=8, null=True, blank=True)
    last_updated = models.CharField(max_length=8, null=True, blank=True)
    e_invoice_status = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.legal_name} - {self.gstin}"

# Return Table
class Return(models.Model):
    company = models.ForeignKey(CompanyDetails, related_name="returns", on_delete=models.CASCADE)
    filing_mode = models.CharField(max_length=20)
    date_of_filing = models.DateField()
    return_type = models.CharField(max_length=20)
    return_period = models.CharField(max_length=10)
    arn = models.CharField(max_length=50)
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.return_type} - {self.arn}"

class CompanyGSTRecord(models.Model):
    gstin = models.CharField(max_length=15)
    legal_name = models.CharField(max_length=255, null=True, blank=True)
    trade_name = models.CharField(max_length=255, null=True, blank=True)
    company_type = models.CharField(max_length=255, null=True, blank=True)
    principal_address = models.JSONField()  # pradr (JSON field for storing address details)
    registration_date = models.CharField(max_length=10, null=True, blank=True)  # rgdt
    last_update = models.CharField(max_length=10, null=True, blank=True)  # lstupdt
    state = models.CharField(max_length=500, null=True, blank=True)
    date_of_filing = models.CharField(max_length=10, null=True, blank=True)
    return_type = models.CharField(max_length=20, null=True, blank=True)
    return_period = models.CharField(max_length=20, null=True, blank=True) # Preference
    return_status = models.CharField(max_length=20, null=True, blank=True)
    additional_data = models.JSONField(null=True, blank=True)  # Store any extra data as JSON
    year = models.CharField(max_length=20, null=True, blank=True) # Get this from 2nd APi out from feild dof 
    month = models.CharField(max_length=20, null=True, blank=True) # Get this from 2nd APi out from feild dof 
    city = models.CharField(max_length=20, null=True, blank=True)
    fetch_date = models.CharField(max_length=20, null=True, blank=True)
    annual_turnover = models.IntegerField(null=True, blank=True)
    delayed_filling = models.CharField(max_length=20, null=True, blank=True)
    Delay_days = models.CharField(max_length=20, null=True, blank=True, default=0)
    result = models.CharField(max_length=10, null=True, blank=True)
    
    def __str__(self):
        return f"{self.legal_name} - {self.gstin}"
    
    
    
class GSTRecord(models.Model):
    gstin = models.CharField(max_length=15, unique=True)
    business_name = models.CharField(max_length=255)
    registration_date = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=50)
    address = models.CharField(max_length=255, blank=True, null=True)
    trade_name = models.CharField(max_length=255, blank=True, null=True)
    company_type = models.CharField(max_length=255, blank=True, null=True)
    filing_status = models.CharField(max_length=50)

class FilingDetails(models.Model):
    gst_record = models.ForeignKey(GSTRecord, on_delete=models.CASCADE)
    return_type = models.CharField(max_length=50)
    filing_period = models.CharField(max_length=10)
    status = models.CharField(max_length=50)
    arn = models.CharField(max_length=50)
    filing_date = models.CharField(max_length=10, null=True, blank=True)

# Score Table
class Score(models.Model):
    company = models.OneToOneField(CompanyDetails, on_delete=models.CASCADE)
    delayed_filing = models.BooleanField(default=False)
    average_delay_days = models.FloatField(default=0.0)

    def __str__(self):
        return f"Score for {self.company.legal_name}"
