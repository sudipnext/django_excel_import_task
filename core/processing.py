import pandas as pd
import time
import os
import json
import gc
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

    import_analytics = ImportAnalytics.objects.create(
        file_name=file_name,
        start_time=timezone.now(),
        status="processing",
    )

    #Initialize the Counts for the import process
    # These will be updated in the import_analytics object
    total_records = 0
    success_count = 0
    warning_count = 0
    failure_count = 0


    #Getting the Chunk Size Variable from the settings
    chunksize = settings.CHUNKSIZE
    start_time_proc = time.time()

    try:
        file_type = "CSV" if is_csv else "Excel"
        DatabaseLogger.log(
            level="INFO",
            message=f"Starting {file_type} import for file: {file_name}",
            task_name=task_name
        )

        # Configure pandas reader with proper options
        if is_csv:
            data_reader = pd.read_csv(
                file_path, 
                chunksize=chunksize, 
                dtype=str, 
                keep_default_na=False,
                low_memory=False
            )
        else:
            data_reader = pd.read_excel(
                file_path, 
                dtype=str, 
                keep_default_na=False
            )

        for chunk_index, chunk in enumerate(data_reader):
            chunk_start_time = time.time()
            chunk_data = chunk.to_dict('records')
            chunk_size_actual = len(chunk_data)
            total_records += chunk_size_actual
            #Logging the Chunk Processing
            DatabaseLogger.log(
                level="INFO", 
                message=f"Processing chunk {chunk_index+1} with {chunk_size_actual} records",
                task_name=task_name
            )
            # Current Import Analytics total records Updated to track the progress
            import_analytics.total_records = total_records
            import_analytics.save(update_fields=['total_records'])

            # Initialize the counters for this chunk and valid records list 
            valid_records_for_bulk = []
            chunk_success = 0
            chunk_warnings = 0
            chunk_failures = 0

            # Process each row in the chunk, row_index is Number and the row_data is the dictionary
            for row_index, row_data in enumerate(chunk_data):
                absolute_row = chunk_index * chunksize + row_index + 1

                # Checking for the mandatory fields that needs to be present for the insertion to work
                required_fields = [
                    'id', 'title', 'description', 'link', 'image_link', 
                    'availability', 'price', 'condition', 'brand', 'gtin'
                ]
                missing_fields = [field for field in required_fields if not row_data.get(field)]

                if missing_fields:
                    #Skipping the row if any of the required fields are missing
                    chunk_failures += 1
                    error_msg = f"Row {absolute_row}: Missing required fields: {', '.join(missing_fields)}"
                    # Logging the error message for the missing fields
                    DatabaseLogger.log(level="ERROR", message=error_msg, task_name=task_name)
                    continue

                #Clearning the data and removing any leading or trailing spaces
                cleaned_data = {k: ('' if pd.isna(v) else str(v).strip()) for k, v in row_data.items()}

                # Handle field mapping to match the Model Serializer 
                if 'id' in cleaned_data:
                    cleaned_data['product_id'] = cleaned_data.pop('id')
                if 'shipping(country:price)' in cleaned_data:
                    cleaned_data['shipping'] = cleaned_data.pop('shipping(country:price)')
                if 'Model' in cleaned_data:
                    cleaned_data['model'] = cleaned_data.pop('Model')

                # Handle JSONField for additional_image_links
                if 'additional_image_links' in cleaned_data and cleaned_data['additional_image_links']:
                    try:
                        # Try parsing as JSON first
                        json.loads(cleaned_data['additional_image_links'])
                    except (ValueError, TypeError):
                        # If not valid JSON, try to convert from comma-separated list
                        try:
                            links = [link.strip() for link in cleaned_data['additional_image_links'].split(',')]
                            cleaned_data['additional_image_links'] = json.dumps(links)
                        except Exception:
                            # If conversion fails, log warning and continue without this field
                            chunk_warnings += 1
                            DatabaseLogger.log(
                                level="WARNING",
                                message=f"Row {absolute_row}: Could not parse additional_image_links: {cleaned_data['additional_image_links']}. Field will be omitted.",
                                task_name=task_name
                            )
                            cleaned_data.pop('additional_image_links', None)

                # Process price fields (critical)
                price_valid = True
                if 'price' in cleaned_data:
                    price_str = str(cleaned_data['price'])
                    if ' ' in price_str:
                        parts = price_str.split(' ', 1)
                        try:
                            cleaned_data['price'] = float(parts[0].replace(',', '.'))
                            cleaned_data['currency'] = parts[1] if len(parts) > 1 else settings.DEFAULT_CURRENCY
                        except ValueError:
                            price_valid = False
                    else:
                        try:
                            cleaned_data['price'] = float(price_str.replace(',', '.'))
                            cleaned_data['currency'] = settings.DEFAULT_CURRENCY
                        except ValueError:
                            price_valid = False

                    if not price_valid:
                        chunk_failures += 1
                        DatabaseLogger.log(
                            level="ERROR",
                            message=f"Row {absolute_row}: Invalid critical price format: {price_str}",
                            task_name=task_name
                        )
                        continue  # Skip row if critical price is invalid

                # Process sale_price (non-critical)
                if 'sale_price' in cleaned_data and cleaned_data['sale_price']:
                    sale_price_str = str(cleaned_data['sale_price'])
                    sale_price_parsed_successfully = False
                    if ' ' in sale_price_str:
                        parts = sale_price_str.split(' ', 1)
                        try:
                            cleaned_data['sale_price'] = float(parts[0].replace(',', '.'))
                            cleaned_data['sale_price_currency'] = parts[1] if len(parts) > 1 else settings.DEFAULT_CURRENCY
                            sale_price_parsed_successfully = True
                        except ValueError:
                            pass
                    else:
                        try:
                            cleaned_data['sale_price'] = float(sale_price_str.replace(',', '.'))
                            cleaned_data['sale_price_currency'] = settings.DEFAULT_CURRENCY
                            sale_price_parsed_successfully = True
                        except ValueError:
                            pass

                    if not sale_price_parsed_successfully:
                        chunk_warnings += 1
                        DatabaseLogger.log(
                            level="WARNING",
                            message=f"Row {absolute_row}: Invalid sale_price format: {sale_price_str}. It will be omitted.",
                            task_name=task_name
                        )
                        cleaned_data.pop('sale_price', None)
                        cleaned_data.pop('sale_price_currency', None)

                # Handling Boolean Field for is_bundle
                if 'is_bundle' in cleaned_data:
                    value = cleaned_data['is_bundle'].lower()
                    if value in ('true', 't', 'yes', 'y', '1'):
                        cleaned_data['is_bundle'] = True
                    elif value in ('false', 'f', 'no', 'n', '0'):
                        cleaned_data['is_bundle'] = False

                # optional_fields = [
                #     'product_length', 'product_width', 'product_height', 
                #     'product_weight', 'lifestyle_image_link', 'max_handling_time'
                # ]
                
                # Track which optional fields were successfully processed
                processed_optional_fields = []
                    
                # Handle max_handling_time (should be an integer)
                if 'max_handling_time' in cleaned_data and cleaned_data['max_handling_time']:
                    try:
                        cleaned_data['max_handling_time'] = int(cleaned_data['max_handling_time'])
                        processed_optional_fields.append('max_handling_time')
                    except ValueError:
                        # Drop the field but don't block insertion
                        DatabaseLogger.log(
                            level="INFO",  # Using INFO level as requested
                            message=f"Row {absolute_row}: Invalid max_handling_time format: {cleaned_data['max_handling_time']}. Field will be omitted.",
                            task_name=task_name
                        )
                        cleaned_data.pop('max_handling_time', None)
                
                # Validate lifestyle_image_link (should be a URL)
                if 'lifestyle_image_link' in cleaned_data and cleaned_data['lifestyle_image_link']:
                    import re
                    url_pattern = re.compile(r'^https?://.+')
                    if url_pattern.match(cleaned_data['lifestyle_image_link']):
                        processed_optional_fields.append('lifestyle_image_link')
                    else:
                        DatabaseLogger.log(
                            level="INFO",
                            message=f"Row {absolute_row}: Invalid lifestyle_image_link format: {cleaned_data['lifestyle_image_link']}. Field will be omitted.",
                            task_name=task_name
                        )
                        cleaned_data.pop('lifestyle_image_link', None)
                
                # Handle dimension fields - they're stored as strings so just validate they're not empty
                for dimension_field in ['product_length', 'product_width', 'product_height', 'product_weight']:
                    if dimension_field in cleaned_data and cleaned_data[dimension_field]:
                        processed_optional_fields.append(dimension_field)
                
                # Log which optional fields were found and processed
                if processed_optional_fields:
                    DatabaseLogger.log(
                        level="INFO",
                        message=f"Row {absolute_row}: Successfully processed optional fields: {', '.join(processed_optional_fields)}",
                        task_name=task_name
                    )

                # Check for recommended fields
                recommended_fields_list = [
                    'description', 'link', 'image_link', 'availability',
                    'condition', 'brand', 'gtin',
                    'sale_price', 'item_group_id', 'google_product_category',
                    'product_type', 'shipping', 'additional_image_links',
                    'size', 'color', 'material', 'pattern', 'gender', 'model'
                ]
                missing_recommended_details = [
                    field for field in recommended_fields_list
                    if not cleaned_data.get(field)
                ]

                # Check for unknown fields not in the model
                model_fields = [f.name for f in Product._meta.get_fields() if hasattr(f, 'name')]
                model_fields.extend(['product_id'])  # 'id' mapped to 'product_id'

                unknown_fields = [field for field in cleaned_data.keys() if field not in model_fields]
                if unknown_fields:
                    chunk_warnings += 1
                    DatabaseLogger.log(
                        level="WARNING",
                        message=f"Row {absolute_row}: Unknown fields will be ignored: {', '.join(unknown_fields)}",
                        task_name=task_name
                    )
                    for field in unknown_fields:
                        cleaned_data.pop(field, None)

                # Create serializer context with currencies if present
                serializer_context = {}
                if 'currency' in cleaned_data:
                    serializer_context['currency'] = cleaned_data['currency']
                if 'sale_price_currency' in cleaned_data:
                    serializer_context['sale_price_currency'] = cleaned_data['sale_price_currency']

                # Validate with serializer
                serializer = ProductSerializer(data=cleaned_data, context=serializer_context)
                
                if serializer.is_valid():
                    valid_records_for_bulk.append({
                        'data': serializer.validated_data,
                        'row': absolute_row,
                        'id': serializer.validated_data.get('product_id')
                    })
                    
                    if missing_recommended_details:
                        chunk_warnings += 1
                        warning_msg = f"Row {absolute_row}: Missing recommended fields: {', '.join(missing_recommended_details)}"
                        DatabaseLogger.log(level="WARNING", message=warning_msg, task_name=task_name)
                else:
                    # Handle validation errors
                    is_row_salvageable = True
                    problematic_fields_log_entries = []
                    core_failure_fields_on_format_error = ['product_id', 'title', 'price']

                    for field, messages in serializer.errors.items():
                        problematic_fields_log_entries.append(f"{field}: {', '.join(messages)}")
                        if field in core_failure_fields_on_format_error:
                            is_row_salvageable = False

                    if is_row_salvageable:
                        # Try partial save with problematic fields removed
                        data_for_partial_save = cleaned_data.copy()
                        for field_with_error in serializer.errors.keys():
                            data_for_partial_save.pop(field_with_error, None)

                        serializer = ProductSerializer(data=data_for_partial_save, context=serializer_context)
                        if serializer.is_valid():  # Revalidate after removing problematic fields
                            valid_records_for_bulk.append({
                                'data': serializer.validated_data,
                                'row': absolute_row,
                                'id': cleaned_data.get('product_id')
                            })
                            
                            format_warning_msg = (
                                f"Row {absolute_row}: Data quality issues ({'; '.join(problematic_fields_log_entries)}). "
                                f"Attempting to save with problematic fields omitted."
                            )
                            DatabaseLogger.log(level="WARNING", message=format_warning_msg, task_name=task_name)
                            chunk_warnings += 1
                        else:
                            # Even after removing problematic fields, it's still not valid
                            chunk_failures += 1
                            error_msg = f"Row {absolute_row}: Could not salvage row even after removing problematic fields"
                            DatabaseLogger.log(level="ERROR", message=error_msg, task_name=task_name)
                    else:
                        # Not salvageable due to critical field format error
                        chunk_failures += 1
                        error_msg = f"Row {absolute_row}: Critical validation failed - {'; '.join(problematic_fields_log_entries)}"
                        DatabaseLogger.log(level="ERROR", message=error_msg, task_name=task_name)

            # Process bulk creation with upsert strategy for duplicates (per chunk)
            if valid_records_for_bulk:
                try:
                    with transaction.atomic():
                        products_to_create = []
                        products_to_update = []
                        product_ids = [r['id'] for r in valid_records_for_bulk if r['id']]
                        
                        # Find existing products to handle duplicates
                        existing_products = {
                            p.product_id: p for p in Product.objects.filter(product_id__in=product_ids)
                        }
                        
                        temp_success_count_for_chunk = 0
                        
                        for record_info in valid_records_for_bulk:
                            try:
                                product_id = record_info['data'].get('product_id')
                                
                                # Ensure essential fields are present
                                if not product_id or \
                                   not record_info['data'].get('title') or \
                                   record_info['data'].get('price') is None:
                                    chunk_failures += 1
                                    DatabaseLogger.log(
                                        level="ERROR",
                                        message=f"Row {record_info['row']}: Missing core fields after validation",
                                        task_name=task_name
                                    )
                                    continue
                                
                                # Check if product already exists (update case)
                                if product_id in existing_products:
                                    existing_product = existing_products[product_id]
                                    for key, value in record_info['data'].items():
                                        setattr(existing_product, key, value)
                                    products_to_update.append(existing_product)
                                else:
                                    # Create new product
                                    products_to_create.append(Product(**record_info['data']))
                                    
                                temp_success_count_for_chunk += 1
                            except Exception as model_instantiation_e:
                                chunk_failures += 1
                                DatabaseLogger.log(
                                    level="ERROR",
                                    message=f"Row {record_info['row']}: Error processing product: {str(model_instantiation_e)}",
                                    task_name=task_name
                                )
                        
                        # Perform bulk operations
                        created_count = 0
                        updated_count = 0
                        
                        if products_to_create:
                            try:
                                created_products = Product.objects.bulk_create(
                                    products_to_create, 
                                    ignore_conflicts=True  # Skip duplicates without failing transaction
                                )
                                created_count = len(created_products)
                            except Exception as create_e:
                                DatabaseLogger.log(
                                    level="ERROR",
                                    message=f"Error in bulk create: {str(create_e)}",
                                    task_name=task_name
                                )
                                raise
                        
                        if products_to_update:
                            try:
                                # Use bulk_update for better performance
                                model_fields_to_update = set()
                                for product in products_to_update:
                                    for field in product.__dict__:
                                        if not field.startswith('_') and field not in ['id', 'created_at', 'updated_at']:
                                            model_fields_to_update.add(field)
                                
                                fields_to_update = list(model_fields_to_update)
                                if fields_to_update and len(products_to_update) > 0:
                                    Product.objects.bulk_update(products_to_update, fields_to_update)
                                updated_count = len(products_to_update)
                            except Exception as update_e:
                                DatabaseLogger.log(
                                    level="ERROR",
                                    message=f"Error in bulk update: {str(update_e)}",
                                    task_name=task_name
                                )
                                raise
                        
                        actual_processed_count = created_count + updated_count
                        chunk_success += actual_processed_count
                        
                        chunk_time = time.time() - chunk_start_time
                        DatabaseLogger.log(
                            level="INFO",
                            message=(f"Chunk {chunk_index+1}: Successfully processed {actual_processed_count} products "
                                    f"({created_count} created, {updated_count} updated) in {chunk_time:.2f}s"),
                            task_name=task_name
                        )
                        
                        if temp_success_count_for_chunk != actual_processed_count:
                            DatabaseLogger.log(
                                level="WARNING",
                                message=f"Chunk {chunk_index+1}: Discrepancy in expected ({temp_success_count_for_chunk}) vs actual ({actual_processed_count}) processed products",
                                task_name=task_name
                            )
                            chunk_failures += (temp_success_count_for_chunk - actual_processed_count)
                
                except Exception as transaction_e:
                    chunk_failures += len(valid_records_for_bulk)
                    DatabaseLogger.log(
                        level="ERROR",
                        message=f"Bulk operation failed for chunk {chunk_index+1}: {str(transaction_e)}",
                        task_name=task_name,
                        error=transaction_e
                    )
            
            # Update overall counters
            success_count += chunk_success
            warning_count += chunk_warnings
            failure_count += chunk_failures
            
            # Update import analytics after each chunk
            import_analytics.success_count = success_count
            import_analytics.warning_count = warning_count
            import_analytics.failure_count = failure_count
            import_analytics.time_taken = time.time() - start_time_proc
            import_analytics.save()
            
            # Free memory between chunks
            del chunk
            if 'chunk_data' in locals():
                del chunk_data
            if 'valid_records_for_bulk' in locals():
                del valid_records_for_bulk
            gc.collect()  # Explicitly request garbage collection

        # Complete the import process
        end_time_proc = time.time()
        time_taken = end_time_proc - start_time_proc

        # Update analytics record with final status
        import_analytics.total_records = total_records
        import_analytics.success_count = success_count
        import_analytics.warning_count = warning_count
        import_analytics.failure_count = failure_count
        import_analytics.end_time = timezone.now()
        import_analytics.time_taken = time_taken
        
        if failure_count == 0:
            import_analytics.status = "completed"
        elif total_records > 0 and success_count == 0:
            import_analytics.status = "failed"
        else:
            import_analytics.status = "completed"
            
        import_analytics.save()

        # Log final status
        DatabaseLogger.log(
            level="INFO",
            message=(f"{file_type} import {import_analytics.status} for {file_name}. "
                    f"Processed: {total_records}, Success: {success_count}, "
                    f"Warnings: {warning_count}, Failures: {failure_count}, "
                    f"Time taken: {time_taken:.2f}s"),
            task_name=task_name
        )

        return {
            'success': total_records > 0 and success_count > 0,
            'message': f"Import {import_analytics.status}",
            'total_records': total_records,
            'success_count': success_count,
            'warning_count': warning_count,
            'failure_count': failure_count,
            'time_taken': time_taken,
            'analytics_id': import_analytics.id
        }

    except pd.errors.EmptyDataError:
        DatabaseLogger.log(
            level="ERROR", 
            message=f"File {file_name} is empty or has no data.", 
            task_name=task_name
        )
        import_analytics.status = "failed"
        import_analytics.end_time = timezone.now()
        import_analytics.save()
        return {'success': False, 'error': f"File {file_name} is empty."}
    except Exception as e:
        DatabaseLogger.log(
            level="CRITICAL",
            message=f"Critical error during data import for {file_name}: {str(e)}",
            task_name=task_name,
            error=e
        )
        import_analytics.end_time = timezone.now()
        import_analytics.time_taken = time.time() - start_time_proc if 'start_time_proc' in locals() else 0
        import_analytics.status = "failed"
        import_analytics.failure_count = total_records - success_count
        import_analytics.save()

        return {
            'success': False,
            'error': str(e)
        }
