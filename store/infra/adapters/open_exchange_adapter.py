import logging
import requests
from decimal import Decimal, ROUND_HALF_UP

from .exchange_rate_port import CurrencyExchangePort

logger = logging.getLogger(__name__)

# Fallback por resiliencia si la red falla
FALLBACK_USD_COP_RATE = Decimal("4200.00")


class OpenExchangeRateAdapter(CurrencyExchangePort):
    """Adaptador estructural que encapsula la API pública de terceros (open.er-api.com).
    Traduce la estructura de datos externa al contrato interno esperado por Bersaj."""

    API_URL = "https://open.er-api.com/v6/latest/USD"

    def __init__(self, timeout=3):
        self.timeout = timeout
        self._cached_rate = None

    def obtener_tasa_usd_a_cop(self) -> Decimal:
        if self._cached_rate:
            return self._cached_rate

        try:
            response = requests.get(self.API_URL, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                cop_rate = rates.get("COP")
                if cop_rate:
                    self._cached_rate = Decimal(str(cop_rate)).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    return self._cached_rate
        except requests.RequestException as e:
            logger.warning(
                f"[ADAPTER TERCEROS] Error consultando API de divisas ({e}). Usando tasa fallback."
            )

        return FALLBACK_USD_COP_RATE

    def convertir_cop_a_usd(self, monto_cop: Decimal) -> Decimal:
        tasa = self.obtener_tasa_usd_a_cop()
        if tasa <= 0:
            return Decimal("0.00")
        
        monto_usd = (monto_cop / tasa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return monto_usd
