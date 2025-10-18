import datetime
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase
import uuid
from django.core.cache import cache

from .models import APIKey
from .enums import IDValidationError
from validator.helper import EgyptianIDValidator, GOVERNORATES


# =============================================================================
# TEST DATA FACTORY & CONSTANTS
# =============================================================================

class TestDataFactory:
    """Factory for creating consistent test data"""
    
    @staticmethod
    def create_valid_national_id(birth_date=None, governorate_code="17", gender="male"):
        """Create a valid national ID for testing"""
        # Base valid ID: Born Mar 27, 2001 (Century 3), Monufia (Code 17), Male
        return "30103271701312"
    
    @staticmethod
    def create_api_key(**kwargs):
        """Create a test API key with consistent defaults"""
        defaults = {
            'name': 'Test API Key',
            'quota_requests_per_minute': 10,
            'quota_requests_per_day': 100
        }
        defaults.update(kwargs)
        
        raw_key = str(uuid.uuid4()).replace('-', '')[:32]
        api_key = APIKey.objects.create(**defaults)
        api_key.set_key(raw_key)
        api_key.prefix_key = raw_key[:8]
        api_key.save()
        
        return api_key, raw_key


# Test Constants
VALID_ID = "30103271701312"
VALID_DATE = datetime.date(2001, 3, 27)
INVALID_CHECKSUM_ID = "29001012100017"
INVALID_LENGTH_ID = "12345"
ARABIC_DIGITS_ID = "٣٠١٠٣٢٧١٧٠١٣١٢"


# =============================================================================
# UNIT TESTS - CORE BUSINESS LOGIC
# =============================================================================

class EgyptianIDValidatorUnitTests(TestCase):
    """Unit tests for the EgyptianIDValidator core logic"""
    
    # -------------------------------------------------------------------------
    # Positive Test Cases
    # -------------------------------------------------------------------------
    
    def test_valid_id_parsing(self):
        """Test successful validation and parsing of a valid ID."""
        is_valid, errors, parsed_data = EgyptianIDValidator.validate_and_parse(
            VALID_ID, strict_checksum=False
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
        self.assertIsNotNone(parsed_data)
        
        self.assertEqual(parsed_data['raw'], VALID_ID)
        self.assertEqual(parsed_data['century_digit'], '3')
        self.assertEqual(parsed_data['birth_date'], VALID_DATE.isoformat())
        self.assertEqual(parsed_data['governorate_code'], '17')
        self.assertEqual(parsed_data['governorate_name'], GOVERNORATES['17'])
        self.assertEqual(parsed_data['serial'], '0131')
        self.assertEqual(parsed_data['gender'], 'male')
        self.assertEqual(parsed_data['checksum_ok'], True)

    def test_arabic_digits_normalization(self):
        """Test Arabic digit normalization works correctly"""
        is_valid, errors, parsed_data = EgyptianIDValidator.validate_and_parse(ARABIC_DIGITS_ID)
        
        self.assertTrue(is_valid)
        self.assertEqual(parsed_data['raw'], VALID_ID)  

    # -------------------------------------------------------------------------
    # Negative Test Cases - Format Validation
    # -------------------------------------------------------------------------
    
    def test_invalid_length(self):
        """Test validation failure for incorrect length."""
        is_valid, errors, parsed_data = EgyptianIDValidator.validate_and_parse(
            INVALID_LENGTH_ID, strict_checksum=False
        )
        
        self.assertFalse(is_valid)
        self.assertIn(IDValidationError.ERR_INVALID_LENGTH.value, errors)
        self.assertIsNone(parsed_data)

    def test_all_zeros_id(self):
        is_valid, errors, parsed_data = EgyptianIDValidator.validate_and_parse("0" * 14)
        self.assertFalse(is_valid)

    def test_sequential_numbers_id(self):
        is_valid, errors, parsed_data = EgyptianIDValidator.validate_and_parse("12345678901234")
        self.assertFalse(is_valid)

    # -------------------------------------------------------------------------
    # Negative Test Cases - Data Validation
    # -------------------------------------------------------------------------
    
    def test_invalid_century(self):
        invalid_century_id = "19001012100018"
        is_valid, errors, parsed_data = EgyptianIDValidator.validate_and_parse(
            invalid_century_id, strict_checksum=False
        )
        
        self.assertFalse(is_valid)
        self.assertIn(IDValidationError.ERR_UNKNOWN_CENTURY.value, errors)

    def test_invalid_date(self):
        invalid_date_id = "29002302100018"
        is_valid, errors, parsed_data = EgyptianIDValidator.validate_and_parse(
            invalid_date_id, strict_checksum=False
        )
        
        self.assertFalse(is_valid)
        self.assertIn(IDValidationError.ERR_INVALID_DATE.value, errors)

    def test_future_date_validation(self):
        future_id = "32601012100018"
        is_valid, errors, parsed_data = EgyptianIDValidator.validate_and_parse(future_id)
        
        self.assertFalse(is_valid)
        self.assertIn(IDValidationError.ERR_FUTURE_DATE.value, errors)

    def test_invalid_governorate(self):
        """Test validation failure for an unknown governorate code."""
        invalid_gov_id = "29001019900018"
        is_valid, errors, parsed_data = EgyptianIDValidator.validate_and_parse(
            invalid_gov_id, strict_checksum=False
        )
        
        self.assertFalse(is_valid)
        self.assertIn(IDValidationError.ERR_UNKNOWN_GOVERNORATE.value, errors)

    def test_checksum_failure_strict(self):
        is_valid, errors, parsed_data = EgyptianIDValidator.validate_and_parse(
            INVALID_CHECKSUM_ID, strict_checksum=True
        )
        
        self.assertFalse(is_valid)
        self.assertIn(IDValidationError.ERR_INVALID_CHECKSUM.value, errors)
        self.assertIsNone(parsed_data)


# =============================================================================
# INTEGRATION TESTS - API ENDPOINTS
# =============================================================================

class ValidateIDViewAuthenticationTests(APITestCase):
    """Tests specifically for authentication and security aspects"""
    
    def setUp(self):
        self.url = reverse('validate-id')
        self.valid_payload = {'national_id': VALID_ID, 'strict_checksum': False}
        self.api_key, self.raw_key = TestDataFactory.create_api_key(
            name="AuthTestKey",
            quota_requests_per_minute=2,
            quota_requests_per_day=10
        )
        self.auth_header = {'HTTP_X_API_KEY': self.raw_key}

    # -------------------------------------------------------------------------
    # Authentication Success Tests
    # -------------------------------------------------------------------------
    
    @patch('validator.views.log_validation_task.delay')
    def test_successful_authentication(self, mock_task):
        """Test successful request with valid API key"""
        response = self.client.post(
            self.url, self.valid_payload, format='json', **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_task.assert_called_once()

    # -------------------------------------------------------------------------
    # Authentication Failure Tests
    # -------------------------------------------------------------------------
    
    @patch('validator.views.log_validation_task.delay')
    def test_access_denied_without_key(self, mock_task):
        """Should be blocked if no API key is provided."""
        response = self.client.post(self.url, self.valid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_task.assert_not_called()

    @patch('validator.views.log_validation_task.delay')
    def test_access_denied_with_invalid_key(self, mock_task):
        """Should be blocked if an invalid API key is provided."""
        invalid_header = {'HTTP_X_API_KEY': 'WrongKey'}
        response = self.client.post(
            self.url, self.valid_payload, format='json', **invalid_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_task.assert_not_called()

    # -------------------------------------------------------------------------
    # Security Tests
    # -------------------------------------------------------------------------
    
    def test_sql_injection_in_api_key_header(self):
        malicious_header = {'HTTP_X_API_KEY': "1' OR '1'='1"}
        response = self.client.post(self.url, self.valid_payload, **malicious_header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_oversized_api_key_header(self):
        oversized_key = 'A' * 10000
        malicious_header = {'HTTP_X_API_KEY': oversized_key}
        response = self.client.post(self.url, self.valid_payload, **malicious_header)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST])


class ValidateIDViewBusinessLogicTests(APITestCase):
    
    def setUp(self):
        self.url = reverse('validate-id')
        self.api_key, self.raw_key = TestDataFactory.create_api_key(
            name="BusinessLogicTestKey"
        )
        self.auth_header = {'HTTP_X_API_KEY': self.raw_key}

    # -------------------------------------------------------------------------
    # Success Scenarios
    # -------------------------------------------------------------------------
    
    @patch('validator.views.log_validation_task.delay')
    def test_successful_validation(self, mock_task):
        valid_payload = {'national_id': VALID_ID, 'strict_checksum': False}
        response = self.client.post(
            self.url, valid_payload, format='json', **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        
        birth_date_response = response.data['parsed']['birth_date']
        if isinstance(birth_date_response, str):
            self.assertEqual(birth_date_response, VALID_DATE.isoformat())
        else:
            self.assertEqual(birth_date_response.isoformat(), VALID_DATE.isoformat())
            
        self.assertEqual(response.data['parsed']['gender'], 'male')

        # Verify logging
        mock_task.assert_called_once()
        call_kwargs = mock_task.call_args[1]
        self.assertEqual(call_kwargs['status_code'], status.HTTP_200_OK)
        self.assertIn('****', call_kwargs['request_data']['national_id'])  # PII masking
        self.assertEqual(call_kwargs['api_key_id'], str(self.api_key.id))

    # -------------------------------------------------------------------------
    # Failure Scenarios
    # -------------------------------------------------------------------------
    
    @patch('validator.views.log_validation_task.delay')
    def test_validation_failure_bad_request(self, mock_task):
        """Test failure due to missing required field in payload"""
        invalid_payload = {'missing_id_field': '29001012100018'}
        response = self.client.post(
            self.url, invalid_payload, format='json', **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])
        self.assertIn('Invalid request:', response.data['errors'][0])

        mock_task.assert_called_once()
        call_kwargs = mock_task.call_args[1]
        self.assertEqual(call_kwargs['status_code'], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(call_kwargs['api_key_id'], str(self.api_key.id))

    @patch('validator.views.log_validation_task.delay')
    def test_validation_failure_invalid_data(self, mock_task):
        invalid_payload = {'national_id': 'invalid-id-text'}
        response = self.client.post(
            self.url, invalid_payload, format='json', **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])


class ValidateIDViewThrottlingTests(APITestCase):
    
    def setUp(self):
        self.url = reverse('validate-id')
        self.valid_payload = {'national_id': VALID_ID, 'strict_checksum': False}
        # Create API key with very low limits for testing
        self.api_key, self.raw_key = TestDataFactory.create_api_key(
            name="ThrottleTestKey",
            quota_requests_per_minute=2,
            quota_requests_per_day=10
        )
        self.auth_header = {'HTTP_X_API_KEY': self.raw_key}
        cache.clear()  # Start with clean cache

    # -------------------------------------------------------------------------
    # Throttling Enforcement Tests
    # -------------------------------------------------------------------------
    
    @patch('validator.views.log_validation_task.delay')
    def test_rate_limit_enforcement(self, mock_task):
        
        # First two requests should succeed
        for i in range(2):
            response = self.client.post(
                self.url, self.valid_payload, format='json', **self.auth_header
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Third request should be throttled
        response = self.client.post(
            self.url, self.valid_payload, format='json', **self.auth_header
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Should only log successful requests (2 calls)
        self.assertEqual(mock_task.call_count, 2)

    def test_rate_limit_accurate_counting(self):
        cache.clear()
        
        successful_requests = 0
        for i in range(10):  
            response = self.client.post(
                self.url, self.valid_payload, format='json', **self.auth_header
            )
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
            successful_requests += 1
            
        self.assertEqual(successful_requests, self.api_key.quota_requests_per_minute)


# =============================================================================
# PERFORMANCE & INTEGRATION TESTS
# =============================================================================

class ValidateIDViewPerformanceTests(APITestCase):
    
    def setUp(self):
        self.url = reverse('validate-id')
        self.api_key, self.raw_key = TestDataFactory.create_api_key()
        self.auth_header = {'HTTP_X_API_KEY': self.raw_key}
        self.valid_payload = {'national_id': VALID_ID, 'strict_checksum': False}

    def test_authentication_performance(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        with CaptureQueriesContext(connection) as context:
            response = self.client.post(
                self.url, self.valid_payload, format='json', **self.auth_header
            )
        
        self.assertLessEqual(len(context), 5)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('validator.views.log_validation_task.delay')
    def test_response_time_acceptable(self, mock_task):
        import time
        
        start_time = time.time()
        response = self.client.post(
            self.url, self.valid_payload, format='json', **self.auth_header
        )
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time_ms, 1000)  # Should respond within 1 second

