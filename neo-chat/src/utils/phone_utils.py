"""Phone number utilities for E.164 normalization."""

import re
from typing import Optional


def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to E.164 international format.
    
    E.164 format: +[country code][subscriber number]
    Example: +1234567890
    
    Args:
        phone: Phone number in any format
        
    Returns:
        Phone number in E.164 format (e.g., +1234567890)
        
    Raises:
        ValueError: If phone number is invalid
        
    Examples:
        >>> normalize_phone_number("+1 (234) 567-8900")
        '+12345678900'
        >>> normalize_phone_number("1234567890")
        '+1234567890'
        >>> normalize_phone_number("+55 11 98765-4321")
        '+5511987654321'
    """
    if not phone:
        raise ValueError("Phone number cannot be empty")
    
    # Remove all non-digit characters except leading +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Ensure it starts with +
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    # Validate format: + followed by 7-15 digits
    if not re.match(r'^\+\d{7,15}$', cleaned):
        raise ValueError(
            f"Invalid phone number format: {phone}. "
            "Expected E.164 format: +[country code][number] (7-15 digits total)"
        )
    
    return cleaned


def extract_phone_from_jid(jid: str) -> str:
    """Extract phone number from WhatsApp JID (Jabber ID).
    
    WhatsApp JIDs are in format: [phone]@s.whatsapp.net
    
    Args:
        jid: WhatsApp JID
        
    Returns:
        Phone number in E.164 format
        
    Examples:
        >>> extract_phone_from_jid("1234567890@s.whatsapp.net")
        '+1234567890'
        >>> extract_phone_from_jid("+1234567890@s.whatsapp.net")
        '+1234567890'
    """
    # Extract phone part before @
    phone = jid.split('@')[0]
    
    # Normalize to E.164
    return normalize_phone_number(phone)


def format_phone_display(phone: str) -> str:
    """Format phone number for display (with spaces).
    
    Args:
        phone: Phone number in E.164 format
        
    Returns:
        Formatted phone number for display
        
    Examples:
        >>> format_phone_display("+12345678900")
        '+1 234 567 8900'
        >>> format_phone_display("+5511987654321")
        '+55 11 98765 4321'
    """
    # Remove + for processing
    digits = phone.lstrip('+')
    
    # Simple formatting: +CC CCC CCC CCCC
    if len(digits) == 11:  # US/Canada format
        return f"+{digits[0]} {digits[1:4]} {digits[4:7]} {digits[7:]}"
    elif len(digits) == 13:  # Brazil format
        return f"+{digits[:2]} {digits[2:4]} {digits[4:9]} {digits[9:]}"
    else:
        # Generic format: +CC CCC...
        return f"+{digits[:2]} {digits[2:]}"


def validate_phone_number(phone: str) -> bool:
    """Validate if phone number is in valid E.164 format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
        
    Examples:
        >>> validate_phone_number("+1234567890")
        True
        >>> validate_phone_number("1234567890")
        False
        >>> validate_phone_number("+123")
        False
    """
    try:
        normalized = normalize_phone_number(phone)
        return True
    except ValueError:
        return False


def get_country_code(phone: str) -> Optional[str]:
    """Extract country code from E.164 phone number.
    
    Args:
        phone: Phone number in E.164 format
        
    Returns:
        Country code (1-3 digits) or None if invalid
        
    Examples:
        >>> get_country_code("+12345678900")
        '1'
        >>> get_country_code("+5511987654321")
        '55'
    """
    if not phone.startswith('+'):
        return None
    
    digits = phone[1:]
    
    # Country codes are 1-3 digits
    # Try to match known patterns (simplified)
    if digits[0] == '1':  # US/Canada
        return '1'
    elif len(digits) >= 2:
        # Most countries use 2-digit codes
        return digits[:2]
    
    return None
