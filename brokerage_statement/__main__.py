import click

from brokerage_statement.factory import brokerage_statement_factory
from brokerage_statement.pdf.models import BrokerageStatementPdf
from brokerage_statement.report.console import calculate_brokerage_statement

# FIXME:  Fix multiple buys and sells (2022.02.04.pdf)
# FIXME:  Fix rule for ISS and Taxa de Corretagem (2022.12.05.pdf)

@click.command()
@click.argument("pdf_path", nargs=1, type=str, required=True)
def main(pdf_path: str):
    with open(pdf_path, "rb") as file:
        pdf_file = file.read()

    pdf_statement = BrokerageStatementPdf(pdf_file)
    brokerage_statement = brokerage_statement_factory(pdf_statement)
    calculate_brokerage_statement(brokerage_statement)


if __name__ == "__main__":
    main()
