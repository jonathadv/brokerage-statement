from brokerage_statement.pdf.utils import PDFDocument, TextBox, TextAlign
from itertools import zip_longest


class FinancialSummaryDescription(TextBox):
    title = "Valor Líquido das Operações(1)"
    width_scale = 1.2


class FinancialSummaryAmount(TextBox):
    title = "Valor Líquido das Operações(1)"
    text_align = TextAlign.TO_THE_RIGHT
    width_scale = 3.0


class FinancialSummary(TextBox):
    title = "Valor Líquido das Operações(1)"
    width_scale = 4.0
    height_scale = 20.0
    text_align = TextAlign.CENTER

    description: FinancialSummaryDescription = FinancialSummaryDescription()
    amount: FinancialSummaryAmount = FinancialSummaryAmount()

    @property
    def table(self) -> tuple[tuple[str, str]]:
        description = self.description.parsed_content
        amount = self.amount.parsed_content
        return tuple(zip_longest(description, amount, fillvalue=""))


class SecurityName(TextBox):
    title = "Especificação do Título"
    text_align = TextAlign.LEFT
    width_scale = 1.0
    height_scale = 20.0
    increase_left = 8.0


class SecurityAmount(TextBox):
    title = "Quantidade"
    text_align = TextAlign.RIGHT
    width_scale = 1.2
    height_scale = 20.0
    increase_right = 1.0


class SecurityPrice(TextBox):
    title = "Preço Liquidação (R$)"
    text_align = TextAlign.RIGHT
    width_scale = 1.0
    height_scale = 20.0
    increase_right = 1.0


class OperationAmount(TextBox):
    title = "Compra/Venda (R$)"
    text_align = TextAlign.RIGHT
    width_scale = 1.0
    height_scale = 20.0
    increase_right = 1.0


class OperationType(TextBox):
    title = "C/V"
    text_align = TextAlign.CENTER
    width_scale = 1.0
    height_scale = 20.0


class StatementDate(TextBox):
    title = "Data pregão"
    text_align = TextAlign.TO_THE_RIGHT
    width_scale = 1.5

    def parsed_content(self) -> list[str]:
        return [self.content.split(":")[1].strip()]


class BrokerageStatementPdf(PDFDocument):
    statement_date: StatementDate = StatementDate()
    security_name: SecurityName = SecurityName()
    security_amount: SecurityAmount = SecurityAmount()
    security_price: SecurityPrice = SecurityPrice()
    operation_amount: OperationAmount = OperationAmount()
    operation_type: OperationType = OperationType()

    financial_summary: FinancialSummary = FinancialSummary()

    @property
    def securities_table(self) -> tuple[tuple[str, str]]:
        security_name = self.security_name.parsed_content
        amount = self.security_amount.parsed_content
        price = self.security_price.parsed_content
        operation_amount = self.operation_amount.parsed_content
        operation_type = self.operation_type.parsed_content

        return tuple(
            zip_longest(
                security_name,
                amount,
                price,
                operation_amount,
                operation_type,
                fillvalue="",
            )
        )
