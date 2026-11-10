from abc import ABC, abstractmethod
from decimal import Decimal


class CurrencyExchangePort(ABC):
    """Contrato abstracto / Puerto (Inversión de Dependencias - DIP).
    Los módulos de alto nivel dependen de esta abstracción, no de la API externa concreta."""

    @abstractmethod
    def obtener_tasa_usd_a_cop(self) -> Decimal:
        """Retorna cuántos COP equivalen a 1 USD."""
        pass

    @abstractmethod
    def convertir_cop_a_usd(self, monto_cop: Decimal) -> Decimal:
        """Convierte una cantidad en COP a su equivalente en USD."""
        pass
