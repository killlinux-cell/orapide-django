import requests
from django.conf import settings

class PayDunyaAPI:
    def __init__(self):
        self.headers = {
            'Content-Type': 'application/json',
            'PAYDUNYA-MASTER-KEY': settings.PAYDUNYA_ACCESS_TOKENS['master_key'],
            'PAYDUNYA-PRIVATE-KEY': settings.PAYDUNYA_ACCESS_TOKENS['private_key'],
            'PAYDUNYA-PUBLIC-KEY': settings.PAYDUNYA_ACCESS_TOKENS['public_key'],
            'PAYDUNYA-TOKEN': settings.PAYDUNYA_ACCESS_TOKENS['token'],
        }
        self.base_url = 'https://app.paydunya.com/api/v1/checkout-invoice/create'
        if settings.PAYDUNYA_MODE == 'test':
            self.base_url = 'https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create'

    def create_invoice(self, invoice_data):
        response = requests.post(self.base_url, json=invoice_data, headers=self.headers)
        return response.json()
