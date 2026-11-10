from decimal import Decimal, ROUND_HALF_UP
from .exchange_rate_port import CurrencyExchangePort


class MockExchangeRateAdapter(CurrencyExchangePort):
    """Adaptador de prueba con tasa fija para tests unitarios deterministas."""

    def __init__(self, fixed_rate=Decimal("4000.00")):
        self.fixed_rate = Decimal(str(fixed_rate))

    def obtener_tasa_usd_a_cop(self) -> Decimal:
        return self.fixed_rate

    def convertir_cop_a_usd(self, monto_cop: Decimal) -> Decimal:
        return (monto_cop / self.fixed_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
