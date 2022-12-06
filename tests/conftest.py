import pytest

@pytest.fixture
def open_pdf():
    def inner(filename: str):
        with open(filename, "rb") as file:
            pdf_file = file.read()
        return pdf_file

    return inner
