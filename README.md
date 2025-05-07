# Task Overview: Import & Process Excel Product Data in Django

## Objective:
To design and implement a Django-based feature that reads and validates an uploaded Excel file containing product data, processes the data efficiently, logs outcomes, and provides analytics through an API.

## Descriptions

### Initial Assessment:
You are given an Excel template with product data. The file may contain hundreds or thousands of rows. You are expected to handle large files safely and efficiently.

### Core Requirements:

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

## Timeline:
This task should be completed within 7 days of the assignment announcement date. You may use any standard Django practices, packages, or patterns. Be prepared to explain your approach, trade-offs, and assumptions during review. The project should be set up in a public GitHub repository, and the link to the repository, as well as the final project deployed link, should be provided by completing the following task form:
https://forms.gle/kdwEpKKD2fUEiq129

## About the template file:
**Template data file link:** https://mr-moving.s3.eu-central-1.amazonaws.com/django_task_data.xlsx

### Must have valid data in column (Mandatory):
id, title, description, link, image_link, availability, price, condition, brand, gtin

### Recommended:
sale_price, item_group_id, google_product_category, product_type, shipping(country:price), additional_image_links, size, color, material, pattern, gender, Model

### Not mandatory (Optional):
product_length, product_width, product_height, product_weight, lifestyle_image_link, max_handling_time, is_bundle
