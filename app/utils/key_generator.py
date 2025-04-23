import secrets
import string

def generate_complex_key(length=32):
    """
    Generate a complex key with specified length containing uppercase letters, 
    lowercase letters, and digits.
    
    Args:
        length: Length of the key to generate (default: 32)
        
    Returns:
        A string containing the generated key
    """
    # Define character sets
    uppercase_letters = string.ascii_uppercase
    lowercase_letters = string.ascii_lowercase
    digits = string.digits
    
    # Ensure at least one character from each set
    key = [
        secrets.choice(uppercase_letters),
        secrets.choice(lowercase_letters),
        secrets.choice(digits)
    ]
    
    # Fill the rest with random characters from all sets
    all_chars = uppercase_letters + lowercase_letters + digits
    key.extend(secrets.choice(all_chars) for _ in range(length - 3))
    
    # Shuffle the characters to avoid predictable patterns
    secrets.SystemRandom().shuffle(key)
    
    # Convert list to string
    return ''.join(key)
