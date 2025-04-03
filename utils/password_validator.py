import re

def validate_password(password):
    """
    Validates that a password meets the required criteria:
    - Minimum length of 6 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one special symbol
    - At least one number
    
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    
    # Check minimum length
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for number
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    # Check for special symbol - any non-alphanumeric character
    if not re.search(r'[^a-zA-Z0-9]', password):
        return False, "Password must contain at least one special symbol"
    
    # All checks passed
    return True, "Password is valid"