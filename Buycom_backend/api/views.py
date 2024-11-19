from rest_framework import viewsets
from .models import Login, CompanyDetails, Return, Score, CompanyGSTRecord
from .serializers import LoginSerializer, CompanyDetailsSerializer, ReturnSerializer, ScoreSerializer, CompanyGSTRecordSerializer
import requests
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from rest_framework.views import APIView
import logging
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.db import IntegrityError  
from datetime import datetime, timedelta
from rest_framework.generics import GenericAPIView
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models.functions import Cast
from django.contrib.auth import logout
from django.db.models import Avg, F, Value, Case, When, IntegerField


# Initialize the logger
logger = logging.getLogger(__name__)

# API credentials
ASP_ID = "1755060724"
PASSWORD = "Cash@2020"
BASE_URL = "https://gstapi.charteredinfo.com/commonapi/v1.1/search"
RETURNS_URL = "https://gstapi.charteredinfo.com/commonapi/v1.0/returns"


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            # Authentication successful
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)

            # Determine user role (for example, "admin" or "user")
            role = 'admin' if user.is_staff else 'user'

            return Response({
                "message": "Login successful",
                "token": token,
                "role": role
            }, status=status.HTTP_200_OK)
        else:
            return Response({"non_field_errors": ["Invalid credentials"]}, status=status.HTTP_400_BAD_REQUEST)
        
@csrf_exempt
@api_view(['POST'])
def logout_view(request):
    # Log the user out
    logout(request)
    return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
def fetch_and_save_gst_record(request):
    gstin = request.data.get('gstin')
    
    if not gstin:
        logger.error("GSTIN is required but not provided.")
        return Response({"error": "GSTIN is required."}, status=400)

    # Fetch the current date for 'fetch_date'
    fetch_date = datetime.today().strftime('%d-%m-%Y')

    # Get 'annual_turnover' from user input, or set it to empty if not provided
    annual_turnover = request.data.get('annual_turnover', '0')
    delayed_filling = request.data.get('delayed_filling', '')
    Delay_days = request.data.get('Delay_days', '')
    result = request.data.get('result', 'N/A')
    
    url1 = f"{BASE_URL}?aspid={ASP_ID}&password={PASSWORD}&Action=TP&Gstin={gstin}"
    response1 = requests.get(url1)
    
    logger.info("Response from first API (status code: %s): %s", response1.status_code, response1.text)

    if response1.status_code == 200:
        gst_data = response1.json()
        if not gst_data:
            logger.error("No data found in first API response.")
            return Response({"error": "No data found in first API response."}, status=500)
    else:
        logger.error("Failed to fetch data from first API.")
        return Response({"error": "Failed to fetch data from first API."}, status=500)

    fy = "2023-24"
    url2 = f"{RETURNS_URL}?aspid={ASP_ID}&password={PASSWORD}&Action=RETTRACK&Gstin={gstin}&fy={fy}"
    response2 = requests.get(url2)
    
    logger.info("Response from second API (status code: %s): %s", response2.status_code, response2.text)

    if response2.status_code == 200:
        data2 = response2.json()
        if "EFiledlist" not in data2:
            logger.error("No 'EFiledlist' field in second API response.")
            return Response({"error": "Invalid response structure from second API."}, status=500)
    else:
        logger.error("Failed to fetch data from second API.")
        return Response({"error": "Failed to fetch data from second API."}, status=500)

    principal_address = gst_data.get("pradr", {})
    registration_date = gst_data.get("rgdt")
    last_update = gst_data.get("lstupdt")

    return_data = data2.get("EFiledlist", [])
    if not return_data:
        logger.error("No valid return data found in second API response.")
        return Response({"error": "No valid return data found in second API response."}, status=500)
    
    for record in return_data:
        return_type = record.get("rtntype")
        date_of_filing = record.get("dof")
        period = record.get("ret_prd", "")
        return_status = request.data.get("status", "Active")
        year = period[2:] if period else ""
        month = period[:2] if period else ""
        
        # Convert dates to strings in the desired format
        try:
            registration_date_str = datetime.strptime(registration_date, '%d/%m/%Y').strftime('%d-%m-%Y') if registration_date else None
            last_update_str = datetime.strptime(last_update, '%d/%m/%Y').strftime('%d-%m-%Y') if last_update else None
            date_of_filing_str = datetime.strptime(date_of_filing, '%d-%m-%Y').strftime('%d-%m-%Y') if date_of_filing else None
        except ValueError as e:
            logger.error(f"Date format error: {e}")
            return Response({"error": "Date format error."}, status=500)

        # Update the state field to use 'loc' from pradr->addr
        state = gst_data.get("pradr", {}).get("addr", {}).get("loc", "N/A")
        city = gst_data.get("pradr", {}).get("addr", {}).get("city", "N/A")
        
        company_gst_record = CompanyGSTRecord.objects.create(
            gstin=gstin,
            legal_name=gst_data.get("lgnm"),
            trade_name=gst_data.get("tradeNam"),
            company_type=gst_data.get("ctb"),
            principal_address=principal_address,
            registration_date=registration_date_str,
            last_update=last_update_str,
            state=state,  # This now uses the 'loc' field
            date_of_filing=date_of_filing_str,
            return_type=return_type,
            return_period=period,
            return_status=return_status,
            year=year,
            month=month,
            city=city,
            fetch_date=fetch_date,  # Use the current date for fetch_date
            annual_turnover=annual_turnover,  # Use the provided or empty annual turnover
            delayed_filling=delayed_filling,
            Delay_days=Delay_days,
            result=result,
            additional_data=gst_data
        )

        logger.info(f"Record saved: {company_gst_record}")

    return Response({"message": "Data fetched and saved successfully."})



@api_view(['PUT'])
def update_gst_record(request):
    gstin = request.data.get('gstin')
    annual_turnover = request.data.get('annual_turnover')
    status = request.data.get('status')

    if not gstin:
        logger.error("GSTIN is required but not provided.")
        return Response({"error": "GSTIN is required."}, status=400)

    # Fetch the records with the specified GSTIN and required return types
    records = CompanyGSTRecord.objects.filter(
        gstin=gstin,
        return_type__in=["GSTR3B", "GSTR1"]
    )

    if not records.exists():
        logger.info(f"No records found for GSTIN {gstin} with required return types.")
        return Response({"message": "No applicable records found."}, status=404)

    # Handle the annual_turnover to ensure it's valid
    if annual_turnover == "" or annual_turnover is None:
        annual_turnover = None  # Set to None for the database
    else:
        try:
            annual_turnover = int(annual_turnover)  # Ensure it's an integer
        except ValueError:
            logger.error(f"Invalid annual_turnover value: {annual_turnover}")
            return Response({"error": "Invalid annual_turnover value."}, status=400)

    # Step 1: Update annual_turnover and status in all records
    for record in records:
        record.annual_turnover = annual_turnover
        if status:
            record.result = status  # Temporary save the status if provided
        record.save()

    # Step 2: Fetch the updated data and apply the business rules
    updated_records = CompanyGSTRecord.objects.filter(
        gstin=gstin,
        return_type__in=["GSTR3B", "GSTR1"]
    )

    def determine_due_date(state, annual_turnover):
        if annual_turnover is None:
            return 20  # Default due date
        if annual_turnover > 5_00_00_000:  # 5 Crore
            return 20
        elif state in ["Chhattisgarh", "Madhya Pradesh", "Gujarat", "Daman and Diu", 
                       "Dadra and Nagar Haveli", "Maharashtra", "Karnataka", "Goa", 
                       "Lakshadweep", "Kerala", "Tamil Nadu", "Puducherry", 
                       "Andaman and Nicobar Islands", "Telangana", "Andhra Pradesh"]:
            return 22
        else:
            return 24

    for record in updated_records:
        try:
            state = record.state
            filing_date = datetime.strptime(record.date_of_filing, "%d-%m-%Y")

            # Set due date based on state and turnover
            due_day = determine_due_date(state, annual_turnover)
            due_date = filing_date.replace(day=due_day)

            # Calculate Delayed filling and Delay days
            delayed_filling = "Yes" if filing_date > due_date else "No"
            delay_days = (filing_date - due_date).days if delayed_filling == "Yes" else 0

            # Ensure Delay_days is treated as an integer
            try:
                delay_days_int = int(record.Delay_days) if record.Delay_days.isdigit() else 0
            except ValueError:
                delay_days_int = 0

            # Update Delay_days with the new value (as an integer in string form)
            record.delayed_filling = delayed_filling
            record.Delay_days = str(delay_days_int)

            # Evaluate result based on delay conditions
            past_year_records = updated_records.filter(
                date_of_filing__gte=datetime.now() - timedelta(days=365)
            )

            # Handle delay calculation using the cleaned Delay_days field
            avg_delay = past_year_records.aggregate(
                avg_delay=Avg(
                    Case(
                        When(Delay_days__regex=r"^\d+$", then=Cast("Delay_days", IntegerField())),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                )
            )["avg_delay"] or 0

            long_delays = past_year_records.filter(
                Delay_days__gt="15"  # String comparison for long delays
            ).count()

            # Determine the last month (immediate past month)
            immediate_past_month = (datetime.now().replace(day=1) - timedelta(days=1)).month

            # Pass or Fail determination
            result = "Pass" if (
                avg_delay <= 7 and long_delays <= 1 and
                all(
                    datetime.strptime(past_record.date_of_filing, "%d-%m-%Y").month != immediate_past_month
                    for past_record in past_year_records
                )
            ) else "Fail"

            # Set the result for the record
            record.result = result
            record.save()

        except Exception as e:
            logger.error(f"Error processing record {record.id}: {e}")
            return Response({"error": f"Error processing record {record.id}: {e}"}, status=500)

    return Response({"message": "GST records updated successfully."})




class LoginViewSet(viewsets.ModelViewSet):
    queryset = Login.objects.all()
    serializer_class = LoginSerializer

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = CompanyGSTRecord.objects.all()
    serializer_class = CompanyGSTRecordSerializer

class CompanyDetailView(APIView):
    def get(self, request, gstin):
        try:
            companies = CompanyGSTRecord.objects.filter(gstin=gstin)  # Use filter() to get multiple records
            if companies.exists():
                serializer = CompanyGSTRecordSerializer(companies, many=True)  # Serialize multiple objects
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "No companies found with the provided GSTIN."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
@api_view(['GET', 'POST'])
def fetch_company_details(request):
    print("POST request received")

    # URL of the external API
    url = "https://gstapi.charteredinfo.com/commonapi/v1.1/search?aspid=1755060724&password=Cash@2020&Action=TP&Gstin=07aagcd1764k1zh"
    
    # Fetch data from the external API
    response = requests.get(url)
    
    if response.status_code == 200:
        print("Data fetched successfully from API")
        full_data = response.json()
        print("Full API Response:", full_data)
        
        # Extract data directly from the full_data response
        registration_date = full_data.get('rgdt', '').replace('/', '')  # Convert to DDMMYYYY format
        last_updated = full_data.get('lstupdt', '').replace('/', '')    # Convert to DDMMYYYY format

        # Attempt to save the data to the database
        try:
            company_details = CompanyDetails.objects.create(
                gstin=full_data.get('gstin', ''),
                legal_name=full_data.get('lgnm', ''),
                trade_name=full_data.get('tradeNam', ''),
                state_jurisdiction_code=full_data.get('stjCd', ''),
                state_jurisdiction=full_data.get('stj', ''),
                central_jurisdiction_code=full_data.get('ctjCd', ''),
                central_jurisdiction=full_data.get('ctj', ''),
                status=full_data.get('sts', ''),
                entity_type=full_data.get('ctb', ''),
                business_nature=full_data.get('nba', []),
                principal_address=full_data.get('pradr', {}),
                registration_date=registration_date,
                last_updated=last_updated,
                e_invoice_status=full_data.get('einvoiceStatus', ''),
            )
            print("Company details saved with ID:", company_details.id)
            return Response({"message": "Data saved successfully", "company_id": company_details.id}, status=201)
        except IntegrityError as e:
            print(f"Integrity error: {e}")
            return Response({"error": "Duplicate entry or constraint violation"}, status=400)
    else:
        print("Failed to fetch data from the API")
        return Response({"error": "Failed to fetch data from the external API"}, status=400)

class ReturnViewSet(viewsets.ModelViewSet):
    queryset = Return.objects.all()
    serializer_class = ReturnSerializer

class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer
