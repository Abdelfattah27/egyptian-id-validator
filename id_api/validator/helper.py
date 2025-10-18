from datetime import date
from typing import Dict, List, Optional, Tuple
from .enums import GOVERNORATES , CENTURY_MAP , IDValidationError
from rest_framework.pagination import LimitOffsetPagination
class EgyptianIDValidator:
    
    @classmethod
    def validate_and_parse(cls, national_id: str, strict_checksum: bool = False) -> Tuple[bool, List[str], Optional[Dict]]:
        """
        Validate Egyptian National ID and extract information
        
        Returns:
            Tuple of (is_valid, errors_list, parsed_data_dict)
        """
        errors = []
        
        national_id = national_id.strip() 
        
        national_id = cls._validate_format(national_id, errors)
        if not national_id:
            return False, errors, None
        
        
        # Extract components
        century_digit = national_id[0]
        year_short = national_id[1:3]
        month = national_id[3:5]
        day = national_id[5:7]
        governorate_code = national_id[7:9]
        serial = national_id[9:13]
        
        # Validate century
        if not cls._validate_century(century_digit, errors):
            return False, errors, None
        
        # Validate date
        birth_date = cls._validate_date(century_digit, year_short, month, day, errors)
        if not birth_date:
            return False, errors, None
        
        # Validate governorate
        governorate_name = cls._validate_governorate(governorate_code, errors)
        
        # Validate checksum 
        checksum_ok = None
        # if strict_checksum:
        checksum_ok = cls._validate_checksum(national_id)
        if strict_checksum and not checksum_ok:
            errors.append(IDValidationError.ERR_INVALID_CHECKSUM.value)
    
        if errors:
            return False, errors, None
        
        age = cls._calculate_age(birth_date)
        
        gender = "male" if int(serial[-1]) % 2 == 1 else "female"
        
        parsed_data = {
            "raw": national_id,
            "century_digit": century_digit,
            "birth_date": birth_date.isoformat(),
            "age": age,
            "governorate_code": governorate_code,
            "governorate_name": governorate_name,
            "serial": serial,
            "gender": gender,
            "checksum_ok": checksum_ok,
        }
        
        return True, errors, parsed_data
    
    @classmethod
    def _validate_format(cls, national_id: str, errors: List[str]) -> bool:
        
        if len(national_id) != 14:
            errors.append(IDValidationError.ERR_INVALID_LENGTH.value)
            return False
        
        normalized = cls._normalize_digits(national_id)
        if not normalized or not normalized.isdigit() or len(normalized) != 14:
            errors.append(IDValidationError.ERR_INVALID_CHARACTERS.value)
            return False
        national_id = normalized
        return national_id
    
    
    @classmethod
    def _normalize_digits(cls, text: str) -> str:
        """Normalize Arabic-digits digits to ASCII digits"""
        
        arabic_digits = "٠١٢٣٤٥٦٧٨٩"
        ascii_digits = "0123456789"
        
        translation_table = str.maketrans(arabic_digits, ascii_digits)
        return text.translate(translation_table)
    
    @classmethod
    def _validate_century(cls, century_digit: str, errors: List[str]) -> bool:
        if century_digit not in CENTURY_MAP:
            errors.append(IDValidationError.ERR_UNKNOWN_CENTURY.value)
            return False
        return True
    
    @classmethod
    def _validate_date(cls, century_digit: str, year_short: str, month: str, day: str, errors: List[str]) -> Optional[date]:
        try:
            full_year = CENTURY_MAP[century_digit] + int(year_short)
            month_int = int(month)
            day_int = int(day)
            
            if month_int < 1 or month_int > 12:
                errors.append(IDValidationError.ERR_INVALID_MONTH.value)
                return None
            
            if day_int < 1 or day_int > 31:
                errors.append(IDValidationError.ERR_INVALID_DAY.value)
                return None
            
            birth_date = date(full_year, month_int, day_int)
            
            if birth_date > date.today():
                errors.append(IDValidationError.ERR_FUTURE_DATE.value)
                return None
                
            return birth_date
            
        except ValueError as e:
            errors.append(IDValidationError.ERR_INVALID_DATE.value)
            return None
    
    @classmethod
    def _validate_governorate(cls, governorate_code: str, errors: List[str]) -> str:
        governorate_name = GOVERNORATES.get(governorate_code, "Unknown")
        if governorate_name == "Unknown":
            errors.append(IDValidationError.ERR_UNKNOWN_GOVERNORATE.value)
        return governorate_name
    
    
    @classmethod
    def _validate_checksum(cls, national_id: str) -> bool:
        try:
            weights = [2, 7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
            total = 0
            
            for i in range(13):
                total += int(national_id[i]) * weights[i]
            
            remainder = total % 11
            check_digit = (11 - remainder) % 10
            
            return check_digit == int(national_id[13])
        except (ValueError, IndexError):
            return False
    
    @classmethod
    def _calculate_age(cls, birth_date: date) -> int:
        today = date.today()
        age = today.year - birth_date.year
        
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
            
        return age
    
    
    
class ValidationLogPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100
    limit_query_param = 'limit'
    offset_query_param = 'offset'