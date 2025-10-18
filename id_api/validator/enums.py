from enum import Enum

GOVERNORATES = {
    # Major Cities
    "01": "Cairo",
    "02": "Alexandria", 
    "03": "Port Said",
    "04": "Suez",
    
    # Delta Governorates
    "11": "Damietta",
    "12": "Dakahlia",
    "13": "Sharqia",
    "14": "Qalyubia",
    "15": "Kafr El Sheikh",
    "16": "Gharbia",
    "17": "Monufia",
    "18": "Beheira",
    "19": "Ismailia",
    
    # Upper Egypt
    "21": "Giza",
    "22": "Beni Suef",
    "23": "Fayoum",
    "24": "Minya",
    "25": "Asyut",
    "26": "Sohag",
    "27": "Qena",
    "28": "Aswan",
    "29": "Luxor",
    
    # Frontier Governorates
    "31": "Red Sea",
    "32": "New Valley",
    "33": "Matrouh",
    "34": "North Sinai",
    "35": "South Sinai",
    
    # Special Codes
    "88": "Foreigner",
}


CENTURY_MAP = {
    "2": 1900,
    "3": 2000,
}


class IDValidationError(Enum):
    ERR_INVALID_LENGTH = "invalid_length"
    ERR_INVALID_CHARACTERS = "invalid_characters"
    ERR_UNKNOWN_CENTURY = "unknown_century"
    ERR_INVALID_MONTH = "invalid_month"
    ERR_INVALID_DAY = "invalid_day"
    ERR_INVALID_DATE = "invalid_date"
    ERR_FUTURE_DATE = "future_date"
    ERR_UNKNOWN_GOVERNORATE = "unknown_governorate"
    ERR_INVALID_CHECKSUM = "invalid_checksum"
    ERR_INVALID_GOVERNORATE_CODE = "invalid_governorate_code"