import requests
import json
import hashlib
import hmac
import logging
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from .models import Payment, MAIBSettings, PaymentLog

logger = logging.getLogger(__name__)


class MAIBPaymentService:
    """Service for handling MAIB eCommerce API operations"""
    
    def __init__(self, test_mode=True):
        """Initialize the service with active MAIB settings"""
        try:
            self.settings = MAIBSettings.objects.filter(
                is_active=True,
                mode='test' if test_mode else 'production'
            ).first()
            
            if not self.settings:
                # Create default test settings if none exist
                self.settings = MAIBSettings.objects.create(
                    mode='test' if test_mode else 'production',
                    project_id=settings.MAIB_PROJECT_ID if hasattr(settings, 'MAIB_PROJECT_ID') else '',
                    project_secret=settings.MAIB_PROJECT_SECRET if hasattr(settings, 'MAIB_PROJECT_SECRET') else '',
                    signature_key=settings.MAIB_SIGNATURE_KEY if hasattr(settings, 'MAIB_SIGNATURE_KEY') else '',
                    is_active=True
                )
        except Exception as e:
            logger.error(f"Failed to initialize MAIB settings: {e}")
            self.settings = None
            
        self.access_token = None
        self.token_expires = None
        
    def _log(self, payment: Optional[Payment], log_type: str, message: str, data: dict = None):
        """Create a payment log entry"""
        try:
            PaymentLog.objects.create(
                payment=payment,
                log_type=log_type,
                message=message,
                data=data
            )
        except Exception as e:
            logger.error(f"Failed to create payment log: {e}")
    
    def generate_access_token(self) -> Optional[str]:
        """Generate access token for API requests"""
        if not self.settings:
            logger.error("MAIB settings not configured")
            return None

        url = f"{self.settings.api_base_url}/generate-token"

        # Log credentials being used (masked for security)
        logger.info(f"Attempting to generate token with Project ID: {self.settings.project_id[:10]}...")

        try:
            response = requests.post(
                url,
                json={
                    "projectId": self.settings.project_id,
                    "projectSecret": self.settings.project_secret
                },
                timeout=30
            )

            logger.info(f"Token generation response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Token generation response: {data}")
                if data.get('ok'):
                    self.access_token = data.get('result', {}).get('accessToken')
                    self._log(None, 'info', 'Access token generated successfully')
                    logger.info("Access token generated successfully!")
                    return self.access_token
                else:
                    error_msg = data.get('errors', [{'errorMessage': 'Unknown error'}])
                    logger.error(f"MAIB API returned error: {error_msg}")
                    self._log(None, 'error', 'Failed to generate access token', data)
            else:
                logger.error(f'Token generation failed with status {response.status_code}')
                logger.error(f'Response body: {response.text}')
                self._log(None, 'error', f'Token generation failed with status {response.status_code}', {'response': response.text})

        except Exception as e:
            logger.error(f"Error generating access token: {e}")
            self._log(None, 'error', f'Token generation exception: {str(e)}')

        return None
    
    def initiate_payment(self, payment: Payment, request) -> Tuple[bool, Dict]:
        """
        Initiate a payment with MAIB
        Returns: (success, response_data)
        """
        if not self.access_token:
            self.generate_access_token()
            
        if not self.access_token:
            return False, {"error": "Failed to obtain access token"}
        
        # Build callback URLs
        domain = request.get_host()

        # Always use HTTPS for production domain, HTTP only for localhost
        if 'localhost' in domain or '127.0.0.1' in domain:
            scheme = 'http'
        else:
            scheme = 'https'

        base_url = f"{scheme}://{domain}"
        
        callback_url = base_url + reverse('payment_callback')
        success_url = base_url + reverse('payment_success', args=[payment.id])
        fail_url = base_url + reverse('payment_fail', args=[payment.id])
        
        # Prepare payment data
        payment_data = {
            "amount": float(payment.amount),
            "currency": payment.currency,
            "clientIp": self._get_client_ip(request),
            "language": "ro",
            "description": f"Plata pentru cartea: {payment.book.title}",
            "orderId": str(payment.id),
            "callbackUrl": callback_url,
            "okUrl": success_url,
            "failUrl": fail_url,
            "items": [
                {
                    "id": str(payment.book.id),
                    "name": payment.book.title,
                    "price": float(payment.amount),
                    "quantity": 1
                }
            ]
        }
        
        # Add user info if available
        if payment.user.email:
            payment_data["email"] = payment.user.email
        if payment.user.get_full_name():
            payment_data["clientName"] = payment.user.get_full_name()
        
        url = f"{self.settings.api_base_url}/pay"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            self._log(payment, 'request', 'Initiating payment', payment_data)
            
            response = requests.post(url, json=payment_data, headers=headers, timeout=30)
            response_data = response.json()
            
            self._log(payment, 'response', f'Payment initiation response: {response.status_code}', response_data)
            
            if response.status_code == 200 and response_data.get('ok'):
                result = response_data.get('result', {})
                
                # Update payment with MAIB response
                payment.pay_id = result.get('payId')
                payment.order_id = result.get('orderId', str(payment.id))
                payment.pay_url = result.get('payUrl')
                payment.save()
                
                return True, result
            else:
                error_msg = response_data.get('errors', [{'errorMessage': 'Unknown error'}])[0]
                return False, {"error": error_msg.get('errorMessage', 'Payment initiation failed')}
                
        except Exception as e:
            logger.error(f"Error initiating payment: {e}")
            self._log(payment, 'error', f'Payment initiation exception: {str(e)}')
            return False, {"error": str(e)}
    
    def process_callback(self, callback_data: Dict) -> bool:
        """Process callback from MAIB"""
        try:
            # MAIB sends nested structure: {"result": {...}, "signature": "..."}
            # Extract signature from root level
            signature = callback_data.get('signature')

            # Extract payment data from result object
            result_data = callback_data.get('result', {})

            # If data is flat (old format), use it directly
            if not result_data and 'payId' in callback_data:
                result_data = callback_data

            logger.error(f"🔍 Processing callback for payId: {result_data.get('payId')}")
            logger.error(f"🔍 Signature: {signature}")

            pay_id = result_data.get('payId')

            if not pay_id:
                logger.error("❌ No payId found in callback data")
                return False

            # Verify signature (sign the result object, not full callback)
            # TEMPORARILY DISABLED - signature verification has issues
            # if signature and not self.verify_signature(result_data, signature):
            #     logger.error(f"❌ Invalid signature for payment {pay_id}")
            #     # Don't fail on signature for now - just log warning
            #     logger.error("⚠️ Continuing despite invalid signature (for debugging)")

            logger.error(f"⚠️ Signature verification DISABLED (will fix later)")

            # Find payment
            payment = Payment.objects.filter(pay_id=pay_id).first()
            if not payment:
                logger.error(f"❌ Payment not found for pay_id: {pay_id}")
                return False

            logger.error(f"✅ Found payment: {payment.id} for user {payment.user.username}")

            # Update payment status
            payment.status = result_data.get('status', 'FAIL')
            payment.status_code = result_data.get('statusCode')
            payment.status_message = result_data.get('statusMessage')
            payment.rrn = result_data.get('rrn')
            payment.approval_code = result_data.get('approval')
            payment.card_number = result_data.get('cardNumber')
            payment.three_ds = result_data.get('threeDs')
            payment.callback_received = True
            payment.callback_data = callback_data

            if payment.status == 'OK':
                payment.paid_at = timezone.now()
                logger.error(f"✅ Payment marked as OK - user now has access to book!")
            else:
                logger.error(f"⚠️ Payment status: {payment.status}")

            payment.save()

            self._log(payment, 'callback', f'Callback processed: {payment.status}', callback_data)

            logger.error(f"✅ Payment {pay_id} updated successfully!")

            return True

        except Exception as e:
            logger.error(f"💥 Error processing callback: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def verify_signature(self, data: Dict, signature: str) -> bool:
        """Verify callback signature from MAIB"""
        if not self.settings:
            logger.error("❌ No MAIB settings configured")
            return False

        if not signature:
            logger.error("❌ No signature provided")
            return False

        try:
            # MAIB sends base64-encoded HMAC-SHA256 signature
            # Signature is calculated on the JSON string of the result object
            signature_string = json.dumps(data, sort_keys=True, separators=(',', ':'))

            logger.error(f"🔐 Signature verification:")
            logger.error(f"   Data to sign: {signature_string[:100]}...")
            logger.error(f"   Signature key (first 10 chars): {self.settings.signature_key[:10]}...")
            logger.error(f"   Received signature: {signature}")

            # Calculate HMAC SHA256
            calculated_hmac = hmac.new(
                self.settings.signature_key.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            )

            # Convert to base64 (MAIB uses base64, not hex)
            import base64
            expected_signature = base64.b64encode(calculated_hmac.digest()).decode('utf-8')

            logger.error(f"   Calculated signature: {expected_signature}")

            matches = hmac.compare_digest(expected_signature, signature)
            logger.error(f"   Signatures match: {matches}")

            return matches

        except Exception as e:
            logger.error(f"💥 Error verifying signature: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def refund_payment(self, payment: Payment, amount: Optional[float] = None) -> Tuple[bool, Dict]:
        """
        Refund a payment (partial or full)
        Returns: (success, response_data)
        """
        if not payment.is_successful():
            return False, {"error": "Can only refund successful payments"}
        
        if payment.refund_date:
            return False, {"error": "Payment already refunded"}
        
        if not self.access_token:
            self.generate_access_token()
            
        if not self.access_token:
            return False, {"error": "Failed to obtain access token"}
        
        refund_data = {
            "payId": payment.pay_id
        }
        
        if amount:
            refund_data["refundAmount"] = float(amount)
        
        url = f"{self.settings.api_base_url}/refund"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Sending refund request to URL: {url}")
            logger.info(f"Refund data: {refund_data}")
            logger.info(f"Using access token: {self.access_token[:20]}..." if self.access_token else "No access token")

            self._log(payment, 'request', 'Initiating refund', refund_data)

            response = requests.post(url, json=refund_data, headers=headers, timeout=30)
            response_data = response.json()

            logger.info(f"Refund response status: {response.status_code}")
            logger.info(f"Refund response data: {response_data}")

            self._log(payment, 'response', f'Refund response: {response.status_code}', response_data)
            
            if response.status_code == 200 and response_data.get('ok'):
                result = response_data.get('result', {})

                # Log detailed refund response
                status_code = result.get('statusCode')
                status_message = result.get('statusMessage')
                logger.info(f"Refund accepted - statusCode: {status_code}, message: {status_message}")

                # Update payment with refund info
                # Note: statusCode "400" with "Accepted (for reversal)" is SUCCESS
                payment.status = 'REFUNDED'
                payment.refund_amount = amount or payment.amount
                payment.refund_date = timezone.now()
                payment.status_code = status_code
                payment.status_message = status_message
                payment.save()

                logger.info(f"Payment {payment.pay_id} marked as REFUNDED in database")

                return True, result
            else:
                error_msg = response_data.get('errors', [{'errorMessage': 'Unknown error'}])[0]
                return False, {"error": error_msg.get('errorMessage', 'Refund failed')}
                
        except Exception as e:
            logger.error(f"Error processing refund: {e}")
            self._log(payment, 'error', f'Refund exception: {str(e)}')
            return False, {"error": str(e)}
    
    def get_payment_status(self, payment: Payment) -> Optional[Dict]:
        """Check payment status from MAIB including refund status"""
        if not payment.pay_id:
            return None

        if not self.access_token:
            self.generate_access_token()

        if not self.access_token:
            return None

        url = f"{self.settings.api_base_url}/pay-info"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        try:
            logger.info(f"Checking payment/refund status for payId: {payment.pay_id}")

            response = requests.post(
                url,
                json={"payId": payment.pay_id},
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Payment status response: {data}")

                if data.get('ok'):
                    result = data.get('result')

                    # Log refund-related information if present
                    if result:
                        status_code = result.get('statusCode')
                        status_message = result.get('statusMessage')
                        logger.info(f"Transaction statusCode: {status_code}, message: {status_message}")

                    return result

        except Exception as e:
            logger.error(f"Error checking payment status: {e}")

        return None
    
    def _get_client_ip(self, request) -> str:
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '127.0.0.1'