from brokerage_statement.factory import brokerage_statement_factory
from brokerage_statement.pdf.models import BrokerageStatementPdf
from brokerage_statement.report import calculate_brokerage_statement

# Fix multiple buys and sells
# "/home/jonatha/Finances/Notas De Corretagem/2022.02.04.pdf"


def main():
    with open(
        "/home/jonatha/Finances/Notas De Corretagem/2022.07.07.pdf", "rb"
    ) as file:
        pdf_file = file.read()

    pdf_statement = BrokerageStatementPdf(pdf_file)
    brokerage_statement = brokerage_statement_factory(pdf_statement)
    calculate_brokerage_statement(brokerage_statement)


if __name__ == "__main__":
    main()
