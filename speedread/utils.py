import re
import unicodedata

def sanitize_filename(filename):
    """
    Convert a string into a safe filename.
    """
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    # Remove non-ASCII characters
    filename = filename.encode('ASCII', 'ignore').decode('ASCII')
    
    # Replace spaces and other unsafe characters
    filename = re.sub(r'[^\w\s-]', '', filename).strip()
    filename = re.sub(r'[-\s]+', '_', filename)
    
    # Ensure the filename is not empty and doesn't start with a dot
    if not filename or filename.startswith('.'):
        filename = '_' + filename
    
    return filename[:255]  # Truncate to a safe length
