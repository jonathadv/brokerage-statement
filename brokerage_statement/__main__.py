import io

import click

from brokerage_statement.factory import brokerage_statement_factory
from brokerage_statement.pdf.models import BrokerageStatementPdf
from brokerage_statement.report.console import calculate_brokerage_statement

# FIXME:  Fix rule for ISS and Taxa de Corretagem (2022.12.05.pdf)


@click.command()
@click.argument("pdf_files", nargs=-1, type=click.File("rb"))
def main(pdf_files: list[io.BufferedReader]):
    pdf_statements = [BrokerageStatementPdf(file.read()) for file in pdf_files]
    brokerage_statement = brokerage_statement_factory(pdf_statements)
    calculate_brokerage_statement(brokerage_statement)


if __name__ == "__main__":
    main()
