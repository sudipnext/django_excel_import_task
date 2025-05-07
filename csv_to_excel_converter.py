import os
import sys
import argparse
import pandas as pd
from pathlib import Path

#!/usr/bin/env python3
"""
CSV to Excel (XLSX) Converter

A utility script for converting CSV files to Excel format.
"""


def convert_csv_to_excel(csv_file_path, output_path=None, sheet_name='Sheet1', index=False):
    """
    Convert a CSV file to Excel (XLSX) format.
    
    Args:
        csv_file_path (str): Path to the CSV file
        output_path (str, optional): Path for the output Excel file.
                                    If not provided, uses same name with .xlsx extension
        sheet_name (str, optional): Name for the Excel sheet. Defaults to 'Sheet1'
        index (bool, optional): Whether to include row indices. Defaults to False
    
    Returns:
        str: Path to the created Excel file
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Determine output filename if not specified
        if output_path is None:
            csv_path = Path(csv_file_path)
            output_path = csv_path.with_suffix('.xlsx')
        
        # Convert to Excel
        df.to_excel(output_path, sheet_name=sheet_name, index=index)
        
        return str(output_path)
    
    except Exception as e:
        print(f"Error converting CSV to Excel: {e}")
        return None


def main():
    """Command line interface for the converter."""
    parser = argparse.ArgumentParser(description='Convert CSV files to Excel (XLSX) format')
    
    parser.add_argument('csv_file', help='Path to the CSV file to convert')
    parser.add_argument('-o', '--output', help='Output Excel file path')
    parser.add_argument('-s', '--sheet', default='Sheet1', help='Name for the Excel sheet')
    parser.add_argument('--with-index', action='store_true', help='Include row indices in Excel file')
    
    args = parser.parse_args()
    
    result = convert_csv_to_excel(
        args.csv_file,
        args.output,
        args.sheet,
        args.with_index
    )
    
    if result:
        print(f"Conversion successful. Excel file created at: {result}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()