import pandas as pd
import time
import os
from django.conf import settings
from django.db import transaction
from core.serializers import ProductSerializer
from core.models import Product, ImportAnalytics
from core.utils import DatabaseLogger
from django.utils import timezone

def process_excel_data(file_path):
    """
    Process an Excel or CSV file by chunks, perform bulk insertions for better performance,
    and log the process including successes, warnings, and errors.
    """
    file_name = os.path.basename(file_path)
    task_name = f"data_import_{file_name}"
    is_csv = file_path.endswith('.csv')
    
    # Create an ImportAnalytics record to track the import
    import_analytics = ImportAnalytics.objects.create(
        file_name=file_name,
        start_time=timezone.now(),
        status="processing",
    )

    # Initialize counters
    total_records = 0
    success_count = 0
    warning_count = 0
    failure_count = 0

    # Set chunk size from settings
    chunksize = settings.CHUNKSIZE
    start_time = time.time()

    try:
        # Log the start of processing
        file_type = "CSV" if is_csv else "Excel"
        DatabaseLogger.log(
            level="INFO",
            message=f"Starting {file_type} import for file: {file_name}",
            task_name=task_name
        )

        # Process data in chunks - we'll count as we go instead of upfront
        data_reader = pd.read_csv(file_path, chunksize=chunksize) if is_csv else pd.read_excel(file_path, chunksize=chunksize)
        
        for chunk_index, chunk in enumerate(data_reader):
            chunk_data = chunk.to_dict('records')
            chunk_size = len(chunk_data)
            total_records += chunk_size  # Count actual processed records

            # Log chunk processing start
            DatabaseLogger.log(
                level="DEBUG",
                message=f"Processing chunk {chunk_index+1} with {chunk_size} records",
                task_name=task_name
            )
            
            # Lists to hold valid records for bulk creation
            valid_records = []
            records_with_warnings = []
            
            # Process each row in the chunk for validation only
            for row_index, row_data in enumerate(chunk_data):
                absolute_row = chunk_index * chunksize + row_index + 1  # +1 for header

                # Check for required fields first (must-have validation)
                required_fields = ['id', 'title', 'price']
                missing_fields = [field for field in required_fields if field not in row_data or pd.isna(row_data.get(field))]

                if missing_fields:
                    failure_count += 1
                    error_msg = f"Row {absolute_row}: Missing required fields: {', '.join(missing_fields)}"
                    DatabaseLogger.log(
                        level="ERROR",
                        message=error_msg,
                        task_name=task_name
                    )
                    continue

                # Warning-level validation (non-blocking)
                recommended_fields = ['description', 'link', 'image_link', 
                                  'availability', 'condition', 'brand', 'gtin']
                missing_recommended_fields = [field for field in recommended_fields if field not in row_data or pd.isna(row_data.get(field))]

                # Handle NaN values from pandas
                cleaned_data = {k: ('' if pd.isna(v) else v) for k, v in row_data.items()}

                if 'id' in cleaned_data:
                    cleaned_data['product_id'] = cleaned_data.pop('id')

                if 'shipping(country:price)' in cleaned_data:
                    cleaned_data['shipping'] = cleaned_data.pop('shipping(country:price)')
                if 'Model' in cleaned_data:
                    cleaned_data['model'] = cleaned_data.pop('Model')
                print("cleaned_data", cleaned_data['price'])
                print("cleaned_data", cleaned_data['sale_price'])
                print("All keys are ", cleaned_data.keys())
                if 'price' in cleaned_data:
                    # Store the original string value containing price and currency
                    price_str = str(cleaned_data['price'])
                    if ' ' in price_str:  # Check if it has space to split
                        parts = price_str.split()
                        cleaned_data['price'] = float(parts[0])
                        cleaned_data['currency'] = parts[1] if len(parts) > 1 else ''
                    else:
                        # Handle case where it's just a number without currency
                        cleaned_data['price'] = float(price_str)
                        cleaned_data['currency'] = ''  # Default currency
                        
                if 'sale_price' in cleaned_data and cleaned_data['sale_price']:
                    # Similar handling for sale_price
                    sale_price_str = str(cleaned_data['sale_price'])
                    if ' ' in sale_price_str:  # Check if it has space to split
                        parts = sale_price_str.split()
                        cleaned_data['sale_price'] = float(parts[0])
                        cleaned_data['sale_price_currency'] = parts[1] if len(parts) > 1 else ''
                    else:
                        # Handle case where it's just a number without currency
                        cleaned_data['sale_price'] = float(sale_price_str)
                        cleaned_data['sale_price_currency'] = ''  # Default currency
                        
                # Validate with serializer but don't save yet
                serializer = ProductSerializer(data=cleaned_data)
                if serializer.is_valid():
                    # Add to valid records list along with row info for logging
                    valid_records.append({
                        'data': serializer.validated_data,
                        'row': absolute_row,
                        'id': cleaned_data.get('product_id')  # Fixed: Use product_id instead of id
                    })
                    
                    # Count warnings if any
                    if missing_recommended_fields:
                        warning_count += 1
                        records_with_warnings.append({
                            'row': absolute_row,
                            'fields': missing_recommended_fields
                        })
                else:
                    failure_count += 1
                    error_details = ', '.join(f"{key}: {', '.join(errors)}" for key, errors in serializer.errors.items())
                    error_msg = f"Row {absolute_row}: Validation failed - {error_details}"
                    DatabaseLogger.log(
                        level="ERROR",
                        message=error_msg,
                        task_name=task_name
                    )
            
            # Bulk insert all valid records in a single transaction
            try:
                with transaction.atomic():
                    # Create objects in bulk
                    products_to_create = [Product(**record['data']) for record in valid_records]
                    
                    if products_to_create:
                        Product.objects.bulk_create(products_to_create)
                        
                        # Log successful imports after bulk operation
                        for record in valid_records:
                            success_count += 1
                            DatabaseLogger.log(
                                level="INFO",
                                message=f"Row {record['row']}: Successfully imported product {record['id']}",
                                task_name=task_name
                            )
                
                # Log warnings after successful bulk insert
                for warning_record in records_with_warnings:
                    warning_msg = f"Row {warning_record['row']}: Missing recommended fields: {', '.join(warning_record['fields'])}"
                    DatabaseLogger.log(
                        level="WARNING",
                        message=warning_msg,
                        task_name=task_name
                    )
                    
            except Exception as e:
                # If bulk insert fails, log it and increment failure count
                failure_count += len(valid_records)
                DatabaseLogger.log(
                    level="ERROR",
                    message=f"Bulk insert failed for chunk {chunk_index+1}: {str(e)}",
                    task_name=task_name,
                    error=e
                )

        # Update import analytics with final, accurate results
        end_time = time.time()
        time_taken = end_time - start_time

        import_analytics.total_records = total_records  # Update with accurate count after processing
        import_analytics.success_count = success_count
        import_analytics.warning_count = warning_count
        import_analytics.failure_count = failure_count
        import_analytics.end_time = timezone.now()
        import_analytics.time_taken = time_taken
        import_analytics.status = "completed"
        import_analytics.save()

        # Log completion
        DatabaseLogger.log(
            level="INFO",
            message=f"{file_type} import completed for {file_name}. "
                    f"Processed: {total_records}, "
                    f"Success: {success_count}, "
                    f"Warnings: {warning_count}, "
                    f"Failures: {failure_count}, "
                    f"Time taken: {time_taken:.2f}s",
            task_name=task_name
        )

        return {
            'success': True,
            'total_records': total_records,
            'success_count': success_count,
            'warning_count': warning_count,
            'failure_count': failure_count,
            'time_taken': time_taken
        }

    except Exception as e:
        # Handle any unexpected exceptions
        DatabaseLogger.log(
            level="CRITICAL",
            message=f"Data import failed for {file_name}",
            task_name=task_name,
            error=e
        )

        # Update import analytics to show failure
        import_analytics.end_time = timezone.now()
        import_analytics.time_taken = time.time() - start_time
        import_analytics.status = "failed"
        import_analytics.save()

        return {
            'success': False,
            'error': str(e)
        }
