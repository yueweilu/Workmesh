#!/usr/bin/env python3
"""
CSV Analyzer - Analyze CSV file data distribution
Auto-generated skill
"""
import sys
import json

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

def analyze_csv(file_path: str) -> dict:
    """Analyze CSV file and return statistics"""
    if not PANDAS_AVAILABLE:
        return {
            "status": "error",
            "error": "pandas is not installed. Install with: pip install pandas"
        }
    
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        
        # Basic statistics
        result = {
            "status": "success",
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data_types": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "sample_data": df.head(5).to_dict(orient='records'),
        }
        
        # Add numeric summary if there are numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            result["numeric_summary"] = df[numeric_cols].describe().to_dict()
        
        return result
    except FileNotFoundError:
        return {
            "status": "error",
            "error": f"File not found: {file_path}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "error": "Missing file_path argument",
            "usage": "python csv_analyzer.py <file_path>"
        }))
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = analyze_csv(file_path)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
