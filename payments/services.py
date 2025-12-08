import requests
import json
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.urls import reverse
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
        
        try:
            response = requests.post(
                url,
                json={
                    "projectId": self.settings.project_id,
                    "projectSecret": self.settings.project_secret
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    self.access_token = data.get('result', {}).get('accessToken')
                    self._log(None, 'info', 'Access token generated successfully')
                    return self.access_token
                else:
                    self._log(None, 'error', 'Failed to generate access token', data)
            else:
                self._log(None, 'error', f'Token generation failed with status {response.status_code}')
                
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
        scheme = 'https' if request.is_secure() else 'http'
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
            pay_id = callback_data.get('payId')
            signature = callback_data.get('signature')
            
            # Verify signature
            if not self.verify_signature(callback_data, signature):
                logger.error(f"Invalid signature for payment {pay_id}")
                return False
            
            # Find payment
            payment = Payment.objects.filter(pay_id=pay_id).first()
            if not payment:
                logger.error(f"Payment not found for pay_id: {pay_id}")
                return False
            
            # Update payment status
            payment.status = callback_data.get('status', 'FAIL')
            payment.status_code = callback_data.get('statusCode')
            payment.status_message = callback_data.get('statusMessage')
            payment.rrn = callback_data.get('rrn')
            payment.approval_code = callback_data.get('approval')
            payment.card_number = callback_data.get('cardNumber')
            payment.three_ds = callback_data.get('threeDs')
            payment.callback_received = True
            payment.callback_data = callback_data
            
            if payment.status == 'OK':
                payment.paid_at = datetime.now()
            
            payment.save()
            
            self._log(payment, 'callback', f'Callback processed: {payment.status}', callback_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing callback: {e}")
            return False
    
    def verify_signature(self, data: Dict, signature: str) -> bool:
        """Verify callback signature from MAIB"""
        if not self.settings:
            return False
            
        # Create signature string from callback data
        # This is a simplified version - check MAIB docs for exact format
        signature_string = json.dumps(data, sort_keys=True)
        
        # Calculate HMAC SHA256
        expected_signature = hmac.new(
            self.settings.signature_key.encode(),
            signature_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
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
            self._log(payment, 'request', 'Initiating refund', refund_data)
            
            response = requests.post(url, json=refund_data, headers=headers, timeout=30)
            response_data = response.json()
            
            self._log(payment, 'response', f'Refund response: {response.status_code}', response_data)
            
            if response.status_code == 200 and response_data.get('ok'):
                result = response_data.get('result', {})
                
                # Update payment with refund info
                payment.status = 'REFUNDED'
                payment.refund_amount = amount or payment.amount
                payment.refund_date = datetime.now()
                payment.save()
                
                return True, result
            else:
                error_msg = response_data.get('errors', [{'errorMessage': 'Unknown error'}])[0]
                return False, {"error": error_msg.get('errorMessage', 'Refund failed')}
                
        except Exception as e:
            logger.error(f"Error processing refund: {e}")
            self._log(payment, 'error', f'Refund exception: {str(e)}')
            return False, {"error": str(e)}
    
    def get_payment_status(self, payment: Payment) -> Optional[Dict]:
        """Check payment status from MAIB"""
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
            response = requests.post(
                url,
                json={"payId": payment.pay_id},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('result')
                    
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