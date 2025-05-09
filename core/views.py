from django.shortcuts import render
import os
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from core.utils import DatabaseLogger
from rest_framework.parsers import MultiPartParser, FormParser
import uuid
from core.processing import process_excel_data
import pandas as pd
import time
from rest_framework.pagination import PageNumberPagination
from core.models import ImportAnalytics, Logs
from core.serializers import ImportAnalyticsSerializer, LogsSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


logger = DatabaseLogger()

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = 'page_size'
    max_page_size = 100  


"""
Django view for Handling Homepage

"""
def index(request):
    return render(request, 'home/index.html')

"""
DRF Viewset for the File Upload and Processing Feature

"""

class FileUploadViewSet(viewsets.ViewSet):
    """
    ViewSet for handling file uploads and processing
    
    """

    parser_classes = (MultiPartParser, FormParser)

    def handle_excel_to_csv_conversion(self, excel_path, csv_path):
        """
        Convert Excel file to CSV format
        Params: 
            excel_path (str): Path to the input Excel file
            csv_path (str): Path to the output CSV file
        Returns:
            bool: True if conversion is successful, False otherwise
        """
        try:
            df = pd.read_excel(excel_path)
            df.to_csv(csv_path, index=False)
            return True
        except Exception as e:
            logger.log(
                level="ERROR",
                message=f"Error converting Excel to CSV: {str(e)}",
                task_name="excel_to_csv_conversion"
            )
            return False



    def create(self, request):
        """Handle file upload"""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES['file']

        # Validate file type
        if not uploaded_file.name.endswith(('.xlsx', '.xls')):
            return Response({'error': 'File must be an Excel file (.xlsx or .xls)'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create a unique filename to prevent overwriting
            unique_id = str(uuid.uuid4())
            excel_filename = f"{unique_id}_{uploaded_file.name}"
            excel_path = os.path.join(settings.MEDIA_ROOT, 'excel_uploads', excel_filename)
            
            # Create CSV filename
            csv_filename = f"{unique_id}_{os.path.splitext(uploaded_file.name)[0]}.csv"
            csv_path = os.path.join(settings.MEDIA_ROOT, 'csv_uploads', csv_filename)

            # Create directories if they don't exist
            os.makedirs(os.path.dirname(excel_path), exist_ok=True)
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)

            # Save the uploaded file
            with open(excel_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Log file upload success
            DatabaseLogger.log(
                level="INFO",
                message=f"Excel file uploaded successfully: {uploaded_file.name}",
                task_name=f"file_upload_{excel_filename}"
            )
            
            # Convert Excel to CSV
            conversion_start = time.time()
            is_conversion_successful = self.handle_excel_to_csv_conversion(excel_path, csv_path)
            if is_conversion_successful:
                # Process the CSV file if conversion was successful
                processing_result = process_excel_data(csv_path)
                processing_result['conversion_time'] = f"{time.time() - conversion_start:.2f} seconds"
            else:
                processing_result = process_excel_data(excel_path)

            # Check if processing was successful
            if not processing_result.get('success', False):
                return Response({
                    'status': 'error',
                    'message': 'File uploaded but processing failed',
                    'error': processing_result.get('error', 'Unknown error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Return success response with processing results
            response_data = {
                'status': 'success',
                'message': 'File uploaded and processed successfully',
                'filename': uploaded_file.name,
                'processing_results': {
                    'total_records': processing_result.get('total_records', 0),
                    'success_count': processing_result.get('success_count', 0),
                    'warning_count': processing_result.get('warning_count', 0),
                    'failure_count': processing_result.get('failure_count', 0),
                    'time_taken': f"{processing_result.get('time_taken', 0):.2f} seconds"
                }
            }
            
            # Add conversion info if available
            if 'conversion_time' in processing_result:
                response_data['processing_results']['conversion_time'] = processing_result['conversion_time']

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the error
            DatabaseLogger.log(
                level="ERROR",
                message=f"Error processing uploaded file: {uploaded_file.name}",
                task_name=f"file_upload_error",
                error=e
            )

            return Response({
                'status': 'error',
                'message': 'An error occurred during file upload or processing',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for import analytics operations"""
    pagination_class = StandardResultsSetPagination


    @swagger_auto_schema(
        operation_summary="Get import analytics",
        manual_parameters=[
            openapi.Parameter('file_name', openapi.IN_QUERY, description="Filter by file name (partial match)", type=openapi.TYPE_STRING),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING, enum=["processing", "failed", "completed"]),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Filter by start date", type=openapi.TYPE_STRING),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="Filter by end date", type=openapi.TYPE_STRING),
            openapi.Parameter('min_success', openapi.IN_QUERY, description="Filter by minimum success count", type=openapi.TYPE_INTEGER),
            openapi.Parameter('min_failure', openapi.IN_QUERY, description="Filter by minimum failure count", type=openapi.TYPE_INTEGER),
        ],
        operation_description="Retrieve import analytics with optional filtering and pagination",
        responses={
            200: ImportAnalyticsSerializer(many=True),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def list(self, request):
        """
        Return the import analytics with filtering options
        Parameters:
            - file_name: Filter by file name (partial match)
            - status: Filter by status (processing, completed, failed)
            - start_date: Filter by start date
            - end_date: Filter by end date
            - min_success: Filter by minimum success count
            - min_failure: Filter by minimum failure count
        
        """
        queryset = ImportAnalytics.objects.all()
        
        # Filter by file name (partial match)
        file_name = request.query_params.get('file_name', None)
        if file_name:
            queryset = queryset.filter(file_name__icontains=file_name)
        
        # Filter by status
        status_param = request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        # Filter by date range
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_time__lte=end_date)
            
        # Filter by success/failure metrics
        min_success = request.query_params.get('min_success', None)
        if min_success and min_success.isdigit():
            queryset = queryset.filter(success_count__gte=int(min_success))
            
        min_failure = request.query_params.get('min_failure', None)
        if min_failure and min_failure.isdigit():
            queryset = queryset.filter(failure_count__gte=int(min_failure))
            
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        serializer = ImportAnalyticsSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class LogsViewSet(viewsets.ViewSet):
    """ViewSet for logs operations"""
    pagination_class = StandardResultsSetPagination


    @swagger_auto_schema(
        operation_summary="Get logs",
        manual_parameters=[
            openapi.Parameter('level', openapi.IN_QUERY, description="Filter by log level", type=openapi.TYPE_STRING, enum=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
            openapi.Parameter('task_name', openapi.IN_QUERY, description="Filter by task name (partial match)", type=openapi.TYPE_STRING),
            openapi.Parameter('message', openapi.IN_QUERY, description="Filter by message content (partial match)", type=openapi.TYPE_STRING),
            openapi.Parameter('created_at', openapi.IN_QUERY, description="Filter by creation date", type=openapi.TYPE_STRING),
        ],
        operation_description="Retrieve logs with optional filtering and pagination",
        responses={
            200: LogsSerializer(many=True),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def list(self, request):
        """Return the logs with filtering options"""
        queryset = Logs.objects.all()
        

        # Filter by creation date
        created_at = request.query_params.get('created_at', None)
        if created_at:
            queryset = queryset.filter(created_at__date=created_at)

        # Filter by log level
        level = request.query_params.get('level', None)
        if level:
            queryset = queryset.filter(level=level)
        
        # Filter by task name (partial match)
        task_name = request.query_params.get('task_name', None)
        if task_name:
            queryset = queryset.filter(task_name__icontains=task_name)
            
        # Filter by message content (partial match)
        message = request.query_params.get('message', None)
        if message:
            queryset = queryset.filter(message__icontains=message)
            
        # Apply pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        serializer = LogsSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
    