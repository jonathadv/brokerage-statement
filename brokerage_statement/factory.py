import re
from decimal import Decimal

from brokerage_statement.models import (
    BrokerageStatement,
    StatementItem,
    OperationType,
    FinancialSummary,
)


def brokerage_statement_factory(pdf_lines: list[str]) -> BrokerageStatement:
    items = _build_statement_items(pdf_lines)
    financial_summary = _build_financial_summary(pdf_lines)

    return BrokerageStatement(
        items=items,
        financial_summary=financial_summary,
    )


def _build_financial_summary(pdf_lines: list[str]) -> FinancialSummary:
    operations_net_value = _parse_operations_net_value(pdf_lines)
    settlement_fee = _parse_settlement_fee(pdf_lines)
    exchange_fees = _parse_exchange_fees(pdf_lines)
    tax_over_service = _parse_tax_over_service(pdf_lines)

    return FinancialSummary(
        operations_net_value=operations_net_value,
        settlement_fee=settlement_fee,
        exchange_fees=exchange_fees,
        tax_over_service=tax_over_service,
    )


def _parse_operations_net_value(pdf_lines: list[str]) -> str:
    return ""


def _parse_settlement_fee(pdf_lines: list[str]) -> Decimal:
    return ""


def _parse_exchange_fees(pdf_lines: list[str]) -> Decimal:
    return ""


def _parse_tax_over_service(pdf_lines: list[str]) -> Decimal:
    return ""


def _build_statement_items(pdf_lines: list[str]) -> list[StatementItem]:
    statement_items: list[StatementItem] = []

    operation_types = _parse_operation_types(pdf_lines)
    tickers = _parse_tickers(pdf_lines)
    amounts = _parse_amounts(pdf_lines)
    settlement_price, buy_sell_price = _parse_prices(pdf_lines)

    assert (
        len(operation_types)
        == len(tickers)
        == len(amounts)
        == len(settlement_price)
        == len(buy_sell_price)
    ), "all StatementItem columns must have the same length"

    for i in range(len(tickers)):

        item = StatementItem(
            operation_type=operation_types[i],
            security=tickers[i],
            amount=amounts[i],
            unit_price=settlement_price[i],
            total_price=buy_sell_price[i],
        )

        assert (
            item.unit_price * item.amount == item.total_price
        ), "unit_price * amount must be equals to total_price"

        statement_items.append(item)

    return statement_items


def _parse_operation_types(pdf_lines: list[str]) -> list[str]:
    lines_between = _sanitize_lines(
        _read_lines_between(
            r".*Especificação do Título.*", r".*Quantidade.*", pdf_lines
        )
    )
    regex = re.compile("1-Bovespa\s+([CV])\s+VIS")
    operation_types: list[str] = []

    for line in lines_between:
        if match := regex.search(line):
            raw_operation_type = match[1].strip()

            if raw_operation_type == "C":
                operation_type = OperationType.BUY
            elif raw_operation_type == "V":
                operation_type = OperationType.SELL
            else:
                raise ValueError(
                    f"Raw Operation Time '{raw_operation_type}' not recognized"
                )

            operation_types.append(operation_type)

    return operation_types


def _parse_prices(pdf_lines: list[str]) -> tuple[list[Decimal], list[Decimal]]:
    lines_between = _sanitize_lines(
        _read_lines_between(
            r".*Preço Liquidação.*", r".*Resumo dos Negócios.*", pdf_lines
        )
    )

    buy_sell_price, settlement_price = _split_list_in_half(lines_between)
    buy_sell_price = [
        buy_sell_price[i] for i in range(len(buy_sell_price)) if i % 2 != 0
    ]
    settlement_price = settlement_price[0::2]

    # convert into Decimal
    settlement_price = [_parse_decimal(i) for i in settlement_price]
    buy_sell_price = [_parse_decimal(i) for i in buy_sell_price]

    return settlement_price, buy_sell_price


def _parse_amounts(pdf_lines: list[str]) -> list[int]:
    lines_between = _read_lines_between(
        r".*Quantidade.*", r".*Preço Liquidação.*", pdf_lines
    )
    amounts = []
    for line in lines_between:
        if line not in [""]:
            amounts.append(line)

    # remove duplicates and convert to int
    amounts = [int(i) for i in amounts[0::2]]
    return amounts


def _parse_tickers(pdf_lines: list[str]) -> list[str]:
    ticker_pattern = r"[A-Z]{4}[\d]{1,2}"
    lines_between = _read_lines_between(
        r".*1-Bovespa C  VIS.*", r".*Quantidade.*", pdf_lines
    )
    tickers: list[str] = []
    for line in lines_between:
        if match := re.search(ticker_pattern, line):
            tickers.append(match[0])
    return tickers


def _read_lines_between(start: str, end: str, pdf_lines: list[str]):
    start_re = re.compile(start)
    end_re = re.compile(end)
    start_idx: int | None = None
    end_idx: int | None = None

    for idx, line in enumerate(pdf_lines):
        if start_re.match(line):
            start_idx = idx
            continue

        if start_idx is not None and end_re.match(line):
            end_idx = idx
            break

    if start_idx is not None and end_idx is not None:
        return pdf_lines[start_idx + 1 : end_idx]

    return []


def _sanitize_lines(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line not in [""]]


def _split_list_in_half(items: list):
    half_len = len(items) // 2

    return [items[x : x + half_len] for x in range(0, len(items), half_len)]


def _parse_decimal(value: str) -> Decimal:
    decimal_separator = ","
    sanitized = re.sub(rf"[^\d{decimal_separator}]", "", value).replace(
        decimal_separator, "."
    )

    return Decimal(sanitized)
