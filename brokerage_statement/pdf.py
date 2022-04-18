from pdfminer.high_level import extract_text


def read_pdf_lines(file_name: str) -> list[str]:
    return extract_text(file_name).split("\n")
