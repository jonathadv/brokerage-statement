from brokerage_statement.models import BrokerageStatement

SEPARATOR = "-" * 170
BOLD = "\u001b[1m"
CLEAN = "\u001b[0m"


def _calculate_report(brokerage_statement: BrokerageStatement) -> list[list[str]]:

    settlement_fee = brokerage_statement.financial_summary.settlement_fee
    exchange_fees = brokerage_statement.financial_summary.exchange_fees
    tax_over_service = brokerage_statement.financial_summary.tax_over_service
    operations_total_amount = brokerage_statement.business_summary.operations_total_amount

    report_rows: list[list[str]] = []

    for item in brokerage_statement.items:
        percent = item.total_price / operations_total_amount
        sec_settlement_fee = settlement_fee * percent
        sec_exchange_fees = exchange_fees * percent
        sec_tax_over_service = tax_over_service * percent

        total_with_fees = sum(
            [
                item.total_price,
                sec_settlement_fee,
                sec_exchange_fees,
                sec_tax_over_service,
            ]
        )

        report_rows.append(
            [
                percent,
                item.security,
                item.amount,
                item.unit_price,
                item.total_price,
                sec_settlement_fee,
                sec_exchange_fees,
                sec_tax_over_service,
                total_with_fees,
                item.operation_type
            ]
        )

    report_rows.append([])
    for column_idx in range(len(report_rows[0])):
        totals = 0

        if isinstance(report_rows[0][column_idx], str):
            report_rows[-1].append("-----")
            continue

        for row in report_rows[:-1]:
            totals += row[column_idx]
        report_rows[-1].append(totals)

    return report_rows


def _draw_report_item_line(report_item: list[str]) -> str:
    return (
        f"{report_item[0] * 100:.2f}%\t\t\t"
        f"{report_item[1]}\t\t\t"
        f"{report_item[2]}\t\t\t\t"
        f"R${report_item[3]}\t\t\t\t"
        f"R${report_item[4]}\t\t"
        f"R${report_item[5]:.2f}\t\t\t\t\t"
        f"R${report_item[6]:.2f}\t\t\t"
        f"R${report_item[7]:.2f}\t\t"
        f"R${report_item[8]:.2f}\t\t\t\t"
        f"{report_item[9].upper()}\t\t"
    )


def calculate_brokerage_statement(brokerage_statement: BrokerageStatement):
    report_items: list[list[str]] = _calculate_report(brokerage_statement)
    operations_net_value = brokerage_statement.financial_summary.operations_net_value

    totals = report_items.pop(-1)

    output: list[str] = []
    output.append(f"{BOLD}DATA:{CLEAN} {brokerage_statement.statement_date:%d/%m/%Y}")
    output.append(
        f"{BOLD}VALOR TOTAL DE OPERAÇÕES:{CLEAN} R$ {operations_net_value:.2f}\n"
    )

    output.append(
        f"{BOLD}"
        "PERCENTAGE\t\t"
        "SECURITY\t\t"
        "QUANTIDADE\t\t"
        "PREÇO UNITÁRIO\t\t"
        "VALOR TOTAL\t\t"
        "TAXA DE LIQUIDAÇÃO\t\t"
        "EMOLUMENTOS\t\t"
        "ISS\t\t\t"
        "TOTAL + TAXAS\t\t\t"
        "OPERAÇÃO\t\t\t"
        f"{CLEAN}"
    )

    for report_item in report_items:
        output.append(_draw_report_item_line(report_item))

    output.append(SEPARATOR)
    output.append(_draw_report_item_line(totals))

    output.insert(0, BOLD + SEPARATOR + CLEAN)
    output.append(BOLD + SEPARATOR + CLEAN)

    print("\n".join(output))
