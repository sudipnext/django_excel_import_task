# Task Overview: Import & Process Excel Product Data in Django

## Objective
To design and implement a Django-based feature that reads and validates an uploaded Excel file containing product data, processes the data efficiently, logs outcomes, and provides analytics through an API.

## Descriptions

### Initial Assessment
You are given an Excel template with product data. The file may contain hundreds or thousands of rows. You are expected to handle large files safely and efficiently.

### Core Requirements

1. **Excel File Handling:**
   - Use `openpyxl` or `pandas` to read the Excel file.
   - Extract and iterate over row data.

2. **Validation Logic:**
   - Implement must-have validation (e.g., SKU, Name, Price). If missing, the row must be rejected with an error.
   - Implement warning-level validation (e.g., missing description or tags), which should not block the insertion but must be logged.

3. **Chunked Data Processing:**
   - Process data in manageable chunks (e.g., 100 rows per batch).
   - Avoid memory overloads when importing large files.

4. **Data Storage:**
   - Save valid rows to the database (e.g., into a `Product` model or similar).
   - Use transactions to handle batch processing.

5. **Logging Requirements:**
   - Maintain logs for:
     - Successful insertions.
     - Warnings (with context).
     - Errors (with reasons and row references).
   - Store logs for later access or auditing.

6. **Analytics API:**
   - Expose an API endpoint to retrieve import results:
     - Total records processed
     - Success count
     - Warning count
     - Failure count
     - Time taken
     - Summary (e.g., types of products inserted)

## Completion Criteria
- ✅ Successful reading and validation of Excel files.
- ✅ Chunk-based row processing with proper logging.
- ✅ Design a proper product database to store product information.
- ✅ Validate and save data for further processing.
- ✅ API available to retrieve summary statistics about the import process.
- ✅ Logs maintained for traceability.

## Timeline
This task should be completed within 7 days of the assignment announcement date. You may use any standard Django practices, packages, or patterns. Be prepared to explain your approach, trade-offs, and assumptions during review. The project should be set up in a public GitHub repository, and the link to the repository, as well as the final project deployed link, should be provided by completing the following task form:
https://forms.gle/kdwEpKKD2fUEiq129

## About the Template File
**Template data file link:** https://mr-moving.s3.eu-central-1.amazonaws.com/django_task_data.xlsx

### Data Field Requirements

#### Must Have (Mandatory)
id, title, description, link, image_link, availability, price, condition, brand, gtin

#### Recommended
sale_price, item_group_id, google_product_category, product_type, shipping(country:price), additional_image_links, size, color, material, pattern, gender, Model

#### Optional
product_length, product_width, product_height, product_weight, lifestyle_image_link, max_handling_time, is_bundle

---

## Implementation Approach

### Overview
This Django application provides a robust Excel file import and processing system for product data. It is designed to efficiently handle large Excel files by using chunked processing, validation, and background task execution with Celery.

### System Architecture

#### Core Components
1. **Django Web Application**
   - Handles file uploads and provides user interface
   - Exposes REST API endpoints for processing status and analytics

2. **Celery Background Processing**
   - Processes large Excel files asynchronously
   - Prevents web server timeouts for large files

3. **Redis**
   - Used as message broker for Celery tasks
   - Enables task queue management and distribution

4. **PostgreSQL Database**
   - Stores product data, logs, and analytics
   - Provides transaction support for reliable data operations

### Key Features

#### Excel File Processing
- **Chunked Processing:** Handles large files (1M+ rows) by processing data in configurable chunks (default: 10,000 rows)
- **Memory Optimization:** Uses pandas with optimized settings to minimize memory usage
- **Progress Tracking:** Real-time progress updates shown to users

#### Validation System
- **Multi-level Validation:**
  - Critical validation for mandatory fields (id, title, price, etc.)
  - Warning-level validation for recommended fields
  - Information-level logging for optional fields
- **Data Salvaging:** Attempts to save records with non-critical validation issues by omitting problematic fields

#### Logging System
- **Database Logging:** All operations are logged to the database for audit and troubleshooting
- **Detailed Context:** Logs include row references, field names, and error details
- **Log Filtering:** UI provides filtering by log level, task name, and message content

#### Analytics
- **Import Analytics:** Tracks metrics for each import operation
- **Real-time Updates:** Analytics are updated during processing
- **Dashboard:** Visual representation of import statistics

### Technical Implementation

#### Data Processing Flow
1. **File Upload:** User uploads Excel file through the web interface
2. **Task Creation:** A Celery task is created and added to the queue
3. **Background Processing:**
   - File is read in chunks using pandas
   - Each row is validated against the Product model requirements
   - Valid records are accumulated for bulk operations
   - Problematic records are logged with appropriate error levels
4. **Bulk Database Operations:**
   - Uses Django's bulk_create and bulk_update for efficiency
   - Transactions ensure data integrity
   - Duplicate handling with upsert strategy

#### Memory Management
The system implements several strategies to manage memory efficiently:
- Chunk-based processing with configurable chunk size
- Explicit garbage collection between chunks
- String handling optimization to minimize memory fragmentation
- Database bulk operations to minimize database roundtrips

#### Error Handling & Recovery
- **Row-Level Error Isolation:** Errors in one row don't affect processing of other rows
- **Transaction Management:** Database operations are wrapped in transactions
- **Task Monitoring:** Failed tasks can be identified and reprocessed

### Deployment Architecture
The application is deployed with the following components:
- Web Server: Gunicorn serving the Django application
- Background Worker: Celery worker process for asynchronous tasks
- Message Broker: Redis for task queue management
- Database: PostgreSQL for data persistence
- Systemd Services: Manages process lifecycle and automatic restarts

### Setup and Installation
To run this system, you'll need:
- Python 3.10+ and a virtual environment
- PostgreSQL database
- Redis server
- Required packages from requirements.txt

The application can be deployed using systemd services for Gunicorn and Celery to ensure reliable operation in production environments.