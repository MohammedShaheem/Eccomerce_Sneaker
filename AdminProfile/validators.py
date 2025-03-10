from decimal import Decimal
from typing import Dict, List, Any, Optional
from django.core.files.uploadedfile import UploadedFile
import re
import os

class FormValidator:
    #general form validator
    
    def __init__(self):
        self.errors: list[str] = []
        
    
    def validate_text_field(
        self,
        value: str,
        field_name: str,
        required: bool = True,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None
    )-> bool:
        value =str(value).strip()
        
        if required and not value:
            self.errors.append(f"{field_name} is required")
            return False
        
        if value:
            if min_length and len(value) < min_length:
                self.errors.append(f"{field_name} must be at least {min_length} charecters long")
                return False
            
            if max_length and len(value) > max_length:
                self.errors.append(f"{field_name} cannot exceed {max_length} characters")
                return False
            
            if pattern and not re.match(pattern, value):
                self.errors.append(f"{field_name} format is invalid")
                return False
            
        return True
    
    def validate_decimal(
        self,
        value: Any,
        field_name: str,
        required: bool = True,
        min_value: Optional[Decimal] = None,
        max_value: Optional[Decimal] = None
    ) -> bool:
        
        if not value and not required:
            return True
        
        try:
            decimal_value = Decimal(str(value))
            
            if min_value is not None and decimal_value < min_value:
                self.errors.append(f"{field_name} must be greater than {min_value}")
                return False
                
            if max_value is not None and decimal_value > max_value:
                self.errors.append(f"{field_name} cannot exceed {max_value}")
                return False
        except (TypeError, ValueError):
            self.errors.append(f"Invalid {field_name} format")
            return False
        
        return True
    
    def validate_integer(
        self,
        value: Any,
        field_name: str,
        required: bool = True,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> bool:
        
        if not value and not required:
            return True
            
        try:
            int_value = int(value)
            
            if min_value is not None and int_value < min_value:
                self.errors.append(f"{field_name} must be greater than {min_value}")
                return False
                
            if max_value is not None and int_value > max_value:
                self.errors.append(f"{field_name} cannot exceed {max_value}")
                return False
                
        except (TypeError, ValueError):
            self.errors.append(f"Invalid {field_name} format")
            return False
            
        return True
    
    def validate_file(
        self,
        file: UploadedFile,
        field_name: str,
        required: bool = True,
        max_size: int = 5 * 1024 * 1024,  # 5MB default
        allowed_types: List[str] = None,
        allowed_extensions: List[str] = None
    ) -> bool:
        if not file:
            if required:
                self.errors.append(f"{field_name} is required")
                return False
            return True
        
        
        _, file_extension = os.path.splitext(file.name)
        file_extension = file_extension.lower()
        
        if allowed_types and not any(file.content_type.startswith(t) for t in allowed_types):
            self.errors.append(f"Invalid file type for {field_name}")
            return False
        
        if allowed_extensions:
            # Ensure all extensions start with a dot
            normalized_extensions = [
                ext if ext.startswith('.') else f'.{ext}'
                for ext in allowed_extensions
            ]
            
            if file_extension not in [ext.lower() for ext in normalized_extensions]:
                allowed_ext_str = ", ".join(normalized_extensions)
                self.errors.append(
                    f"Invalid file extension for {field_name}. Allowed extensions: {allowed_ext_str}"
                )
                return False
        
        if file.size > max_size:
            self.errors.append(f"{field_name} exceeds maximum size of {max_size/1024/1024}MB")
            return False
            
        return True
    
    def get_errors(self) -> List[str]:
        return self.errors
            