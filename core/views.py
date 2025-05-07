from django.shortcuts import render
import os
from django.conf import settings
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from core.utils import DatabaseLogger
from rest_framework.parsers import MultiPartParser, FormParser
import uuid
from core.processing import process_excel_data
import pandas as pd
import time
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.dateparse import parse_datetime
from rest_framework.filters import OrderingFilter

logger = DatabaseLogger()

def index(request):
    return render(request, 'home/index.html')

class FileUploadViewSet(viewsets.ViewSet):
    """ViewSet for file upload operations"""

    parser_classes = (MultiPartParser, FormParser)

    def list(self, request):
        """Return the upload form"""
        return render(request, 'upload_form.html')

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
            try:
                df = pd.read_excel(excel_path)
                df.to_csv(csv_path, index=False)
                conversion_time = time.time() - conversion_start
                
                # Log conversion success
                DatabaseLogger.log(
                    level="INFO",
                    message=f"Excel file converted to CSV: {csv_filename}",
                    task_name=f"file_conversion_{unique_id}"
                )
            except Exception as e:
                # If conversion fails, use the original Excel file
                DatabaseLogger.log(
                    level="WARNING",
                    message=f"Failed to convert Excel to CSV: {str(e)}",
                    task_name=f"file_conversion_{unique_id}",
                    error=e
                )
                # Process the original Excel file instead
                processing_result = process_excel_data(excel_path)
            else:
                # Process the CSV file if conversion was successful
                processing_result = process_excel_data(csv_path)
                processing_result['conversion_time'] = f"{conversion_time:.2f} seconds"

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


from core.models import ImportAnalytics, Logs
from core.serializers import ImportAnalyticsSerializer, LogsSerializer

class AnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for import analytics operations"""

    def list(self, request):
        """Return the import analytics with filtering options"""
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
            
        # Ordering
        order_by = request.query_params.get('order_by', '-created_at')
        queryset = queryset.order_by(order_by)
        
        serializer = ImportAnalyticsSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get a specific analytics record by ID"""
        try:
            analytics = ImportAnalytics.objects.get(pk=pk)
            serializer = ImportAnalyticsSerializer(analytics)
            return Response(serializer.data)
        except ImportAnalytics.DoesNotExist:
            return Response(
                {"error": "Analytics record not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class LogsViewSet(viewsets.ViewSet):
    """ViewSet for logs operations"""

    def list(self, request):
        """Return the logs with filtering options"""
        queryset = Logs.objects.all()
        
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
            
        # Filter by error presence
        has_error = request.query_params.get('has_error', None)
        if has_error and has_error.lower() == 'true':
            queryset = queryset.exclude(traceback__isnull=True).exclude(traceback='')
        
        # Pagination
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 100)
        try:
            page = int(page)
            page_size = min(int(page_size), 100)  # Limit max page size
            start = (page - 1) * page_size
            end = page * page_size
            queryset = queryset.order_by('-id')[start:end]
        except ValueError:
            queryset = queryset.order_by('-id')[:100]
        
        serializer = LogsSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get a specific log record by ID"""
        try:
            log = Logs.objects.get(pk=pk)
            serializer = LogsSerializer(log)
            return Response(serializer.data)
        except Logs.DoesNotExist:
            return Response(
                {"error": "Log record not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )