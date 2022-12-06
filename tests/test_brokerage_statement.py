import pytest

from brokerage_statement.factory import brokerage_statement_factory
from brokerage_statement.pdf.models import BrokerageStatementPdf


@pytest.mark.skip
def test_multiple_buys(open_pdf, snapshot):
    pdf_file = open_pdf("pdf_file")

    pdf_statement = BrokerageStatementPdf(pdf_file)

    brokerage_statement = brokerage_statement_factory(pdf_statement)

    snapshot.assert_match(brokerage_statement.json())
