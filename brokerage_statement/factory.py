import re
from decimal import Decimal
from datetime import datetime

from brokerage_statement.pdf.models import BrokerageStatementPdf
from brokerage_statement.models import (
    BrokerageStatement,
    StatementItem,
    OperationType,
    FinancialSummary,
    BusinessSummary,
)


def brokerage_statement_factory(
    pdf_statement: BrokerageStatementPdf,
) -> BrokerageStatement:
    brokerage_statement = BrokerageStatement(
        statement_date=_parse_statement_date(pdf_statement),
        items=_build_statement_items(pdf_statement),
        business_summary=_build_business_summary(pdf_statement),
        financial_summary=_build_financial_summary(pdf_statement),
        net_price=_parse_net_price(pdf_statement),
    )

    assert brokerage_statement.business_summary.operations_total_amount == sum(
        map(lambda x: x.total_price, brokerage_statement.items)
    ), "operations_total_amount != sum(items.total_price)"
    return brokerage_statement


def _parse_statement_date(pdf_statement: BrokerageStatementPdf) -> datetime:
    return datetime.strptime(
        pdf_statement.statement_date.parsed_content()[0], "%d/%m/%Y"
    )


def _parse_net_price(pdf_statement: BrokerageStatementPdf) -> Decimal:
    for item, value in reversed(pdf_statement.financial_summary.table):
        if item.strip().startswith("Liquido para"):
            return _parse_decimal(value)
    raise ValueError(f"Net Price not found in '{pdf_statement.financial_summary}'")


def _build_financial_summary(pdf_statement: BrokerageStatementPdf) -> FinancialSummary:
    items = dict(pdf_statement.financial_summary.table)
    operations_net_value: Decimal = _parse_decimal(
        items.get("Valor Líquido das Operações(1)")
    )
    settlement_fee: Decimal = _parse_decimal(items.get("Taxa de Liquidação(2)"))
    exchange_fees: Decimal = _parse_decimal(items.get("Emolumentos"))
    tax_over_service: Decimal = _parse_decimal(items.get("ISS"))

    return FinancialSummary(
        operations_net_value=operations_net_value,
        settlement_fee=settlement_fee,
        exchange_fees=exchange_fees,
        tax_over_service=tax_over_service,
    )


def _build_business_summary(pdf_statement: BrokerageStatementPdf) -> BusinessSummary:
    return BusinessSummary(
        operations_total_amount=_parse_decimal(
            pdf_statement.business_summary.operations_total_amount.parsed_content[0]
        )
    )


def _build_statement_items(pdf_statement: BrokerageStatementPdf) -> list[StatementItem]:
    statement_items: list[StatementItem] = []

    for (
        security_name,
        amount,
        price,
        operation_amount,
        operation_type,
    ) in pdf_statement.securities_table:

        if _should_skip_line(security_name):
            continue

        item = StatementItem(
            operation_type=_parse_operation_type(operation_type.strip()),
            security=security_name.split()[0].strip(),
            amount=amount.strip().replace(".", ""),
            unit_price=_parse_decimal(price),
            total_price=_parse_decimal(operation_amount),
        )

        assert (
            item.unit_price * item.amount == item.total_price
        ), "unit_price * amount must be equals to total_price"

        statement_items.append(item)

    return statement_items


def _should_skip_line(security_name: str) -> bool:
    value = security_name.strip().lower()
    return any([value.startswith("subtotal"), value.startswith("especificação")])


def _parse_operation_type(raw_op_type):
    if raw_op_type == "C":
        return OperationType.BUY
    if raw_op_type == "V":
        return OperationType.SELL
    raise ValueError(f"Invalid operation type '{raw_op_type}'")


def _parse_decimal(value: str) -> Decimal:
    decimal_separator = ","
    sanitized = re.sub(rf"[^\d{decimal_separator}]", "", value).replace(
        decimal_separator, "."
    )

    return Decimal(sanitized)
