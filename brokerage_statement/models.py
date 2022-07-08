from decimal import Decimal
from enum import Enum

from pydantic import BaseModel
from datetime import datetime


class OperationType(str, Enum):
    SELL = "sell"
    BUY = "buy"


class StatementItem(BaseModel):
    operation_type: OperationType
    security: str
    amount: int
    unit_price: Decimal
    total_price: Decimal


class FinancialSummary(BaseModel):
    # Valor líquido das operações
    operations_net_value: Decimal
    # Taxa de Liquidação
    settlement_fee: Decimal
    # Emolumentos
    exchange_fees: Decimal
    # Imposto sobre Serviço (ISS)
    tax_over_service: Decimal


class BusinessSummary(BaseModel):
    # Valor das Operações
    operations_total_amount: Decimal


class BrokerageStatement(BaseModel):
    statement_date: datetime
    items: list[StatementItem] = []
    financial_summary: FinancialSummary
    business_summary: BusinessSummary
    net_price: Decimal
