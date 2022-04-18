__version__ = "0.1.0"


from brokerage_statement.factory import brokerage_statement_factory
from brokerage_statement.pdf import read_pdf_lines

pdf_lines = read_pdf_lines("/home/jonatha/2022.04.13.pdf")
brokerage_statement = brokerage_statement_factory(pdf_lines)
assert brokerage_statement
