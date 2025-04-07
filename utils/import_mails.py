from flask import Flask, request, jsonify
import os
import sys
import subprocess
from werkzeug.utils import secure_filename
import re  # Add this import at the top with other imports
import pandas as pd
app = Flask(__name__, static_folder='.', static_url_path='')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv'}

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check and install required dependencies
required_packages = ['pandas', 'openpyxl', 'xlrd']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_emails_from_dataframe(df):
    """
    Extract email addresses from all cells in a DataFrame
    Returns a list of unique email addresses
    """
    emails = set()
    
    # Convert all DataFrame values to strings and search for emails
    for column in df.columns:
        for value in df[column].astype(str):
            # Find all strings that match the pattern *@*.com
            found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', value)
            for email in found_emails:
                emails.add(email.lower())  # Convert to lowercase for deduplication
    
    return sorted(list(emails))  # Return sorted list of unique emails

def process_excel_file(file):
    """
    Process the uploaded Excel file and extract information
    """
    try:
        if not file or file.filename == '':
            return {
                "success": False,
                "message": "No file selected"
            }, 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Check if file is excel or csv
            if filename.endswith(('.xlsx', '.xls', '.csv')):
                try:
                    if filename.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    elif filename.endswith('.xls'):
                        df = pd.read_excel(file_path, engine='xlrd')
                    else:  # .xlsx
                        df = pd.read_excel(file_path, engine='openpyxl')
                    
                    # Get the column names and first few rows
                    columns = df.columns.tolist()
                    preview = df.head(5).to_dict(orient='records')
                    row_count = len(df)
                    
                    # Extract email addresses from the dataframe
                    extracted_emails = extract_emails_from_dataframe(df)
                    print(f"Found {len(extracted_emails)} unique email addresses")
                    
                    return {
                        "success": True,
                        "message": "Excel file read successfully",
                        "filename": filename,
                        "columns": columns,
                        "preview": preview,
                        "row_count": row_count,
                        "extracted_emails": extracted_emails,
                        "email_count": len(extracted_emails)
                    }, 200
                except ImportError as e:
                    missing_package = 'openpyxl' if filename.endswith('.xlsx') else 'xlrd'
                    installation_cmd = f"pip install {missing_package}"
                    error_msg = f"Missing dependency to read {filename.split('.')[-1]} files. Please run '{installation_cmd}'"
                    print(error_msg)
                    
                    # Try to install the missing package automatically
                    try:
                        print(f"Attempting to install {missing_package}...")
                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', missing_package])
                        print(f"Successfully installed {missing_package}")
                        
                        # Retry reading the file after installing the package
                        if filename.endswith('.csv'):
                            df = pd.read_csv(file_path)
                        elif filename.endswith('.xls'):
                            import importlib
                            importlib.reload(pd)
                            df = pd.read_excel(file_path, engine='xlrd')
                        else:  # .xlsx
                            import importlib
                            importlib.reload(pd)
                            df = pd.read_excel(file_path, engine='openpyxl')
                        
                        columns = df.columns.tolist()
                        preview = df.head(5).to_dict(orient='records')
                        row_count = len(df)
                        
                        # Extract email addresses from the dataframe
                        extracted_emails = extract_emails_from_dataframe(df)
                        print(f"Found {len(extracted_emails)} unique email addresses")
                        
                        return {
                            "success": True,
                            "message": f"Installed {missing_package} and read Excel file successfully",
                            "filename": filename,
                            "columns": columns,
                            "preview": preview,
                            "row_count": row_count,
                            "extracted_emails": extracted_emails,
                            "email_count": len(extracted_emails)
                        }, 200
                    except Exception as install_error:
                        return {
                            "success": False,
                            "message": f"Failed to install {missing_package}. Please run '{installation_cmd}' manually. Error: {str(install_error)}"
                        }, 400
                
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Failed to read Excel file: {str(e)}"
                    }, 400
            else:
                return {
                    "success": False,
                    "message": "Uploaded file is not an Excel or CSV file"
                }, 400
        else:
            return {
                "success": False,
                "message": "File type not allowed"
            }, 400
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to process Excel file: {str(e)}"
        }, 500

@app.route('/read-excel', methods=['POST'])
def read_excel():
    return process_excel_file(request.files.get('file'))

