from brokerage_statement.models import BrokerageStatement

SEPARATOR = "-" * 170
BOLD = "\u001b[1m"
CLEAN = "\u001b[0m"
TABLE_HEADER_TEMPLATE = "{: >15.2f} {: >10} {: >15} {: >15} {: >15} {: >20.2f} {: >15.2f} {: >8.2f} {: >17.2f} {: >10}"


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
    return TABLE_HEADER_TEMPLATE.format(
        report_item[0] * 100,
        report_item[1],
        report_item[2],
        report_item[3],
        report_item[4],
        report_item[5],
        report_item[6],
        report_item[7],
        report_item[8],
        report_item[9]
    ).replace(".", ",")



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
     BOLD + TABLE_HEADER_TEMPLATE.replace(".2f", "").format(
        "PERCENTAGE",
        "ATIVO",
        "QUANTIDADE",
        "PREÇO UNITÁRIO",
        "VALOR TOTAL",
        "TAXA DE LIQUIDAÇÃO",
        "EMOLUMENTOS",
        "ISS",
        "TOTAL + TAXAS",
        "OPERAÇÃO",
    ) + CLEAN)

    for report_item in report_items:
        output.append(_draw_report_item_line(report_item))

    output.append(SEPARATOR)
    output.append(_draw_report_item_line(totals))

    output.insert(0, BOLD + SEPARATOR + CLEAN)
    output.append(BOLD + SEPARATOR + CLEAN)

    print("\n".join(output))
