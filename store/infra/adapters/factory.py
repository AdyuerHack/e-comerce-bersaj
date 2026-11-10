import os
from .exchange_rate_port import CurrencyExchangePort
from .open_exchange_adapter import OpenExchangeRateAdapter
from .mock_exchange_adapter import MockExchangeRateAdapter


class CurrencyAdapterFactory:
    """Fábrica para inyectar la implementación del Adapter requerida."""

    @staticmethod
    def get_adapter() -> CurrencyExchangePort:
        mode = os.getenv("EXCHANGE_API_MODE", "REAL").upper()
        if mode == "MOCK":
            return MockExchangeRateAdapter()
        return OpenExchangeRateAdapter()
