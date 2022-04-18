import re
from enum import Enum
from io import BytesIO
from typing import Iterable, cast

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTAnno, LTChar, LTComponent
from pdfminer.high_level import extract_text
from pydantic import BaseModel, PrivateAttr

PDFPageChars = list[LTChar | LTAnno]


class PDFModel(BaseModel):
    _file: bytes = PrivateAttr()
    pdf_pages: list[PDFPageChars] = []
    pdf_lines: list[str] = []

    def __init__(self, pdf_file: bytes):
        super().__init__()
        self._file = pdf_file
        pdf_file = BytesIO(pdf_file)
        self.pdf_pages = self._extract_pdf_pages(pdf_file)
        self.pdf_lines = extract_text(pdf_file).split("\n")

    def _extract_pdf_pages(self, pdf_file: BytesIO) -> list[PDFPageChars]:
        pdf_pages: list[PDFPageChars] = []
        raw_pages = extract_pages(pdf_file)

        for raw_page in raw_pages:
            pdf_page = []
            for raw_elem in raw_page:
                for text_elem in self._extract_pdf_page_elements(raw_elem):
                    if isinstance(text_elem, (LTChar, LTAnno)):
                        pdf_page.append(text_elem)

            pdf_pages.append(pdf_page)

        return pdf_pages

    def _extract_pdf_page_elements(
        self, page_element: LTComponent
    ) -> list[LTComponent]:
        page_elements = [page_element]

        if isinstance(page_element, Iterable):
            for inner_element in page_element:
                page_elements.extend(self._extract_pdf_page_elements(inner_element))

        return page_elements

    def get_lines_between(self, start_regex: str, end_regex: str) -> list[str]:
        return get_lines_between(
            start_regex,
            end_regex,
            self.pdf_lines,
        )

    class Config:
        arbitrary_types_allowed = True


class PDFDocument(PDFModel):
    """A model that accepts TextBox fields"""

    def __init__(self, input_file: bytes):
        super().__init__(input_file)

        for field in self.__fields__:
            instance = getattr(self, field)
            if isinstance(instance, TextBox):
                instance.load_content(self.pdf_pages)


class Boundary(BaseModel):
    left: float | None = None
    right: float | None = None
    top: float | None = None
    bottom: float | None = None
    page_index: int = 0


class TextAlign(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    #
    TO_THE_RIGHT = "to_the_right"


class TextBoxLayout(BaseModel):
    char_height: float = 7.0
    word_margin_range: tuple[float, float] = (0.7, 0.8)
    text_align: TextAlign = TextAlign.LEFT
    width_scale: float = 1.0
    height_scale: float = 1.0
    increase_left: float = 0.1
    increase_right: float = 0.1

    def _get_line_breaks_count(self, prev: LTChar, current: LTChar) -> int:
        char_margin = prev.y0 - current.y1

        word_margin_min, word_margin_max = self.word_margin_range

        # if the char margin is within the range, it means only one line break (\n)
        if word_margin_min < char_margin < word_margin_max:
            return 1

        # determine how many line breaks are withing the char_margin
        if char_margin > word_margin_max:
            return int(char_margin / self.char_height) + 1

        return 0

    def _fix_line_breaks(self, characters: list[LTChar]) -> list[LTChar | str]:
        # Replace the line breaks created by PDFMiner by more accurate ones.
        content: list[LTChar | str] = []

        found_new_line = False
        for char in characters:
            if isinstance(char, LTChar):
                if content and content[-1].get_text() == " ":
                    found_new_line = False
                    content.append(char)
                    continue

                if found_new_line:
                    found_new_line = False
                    linebreak_amount = self._get_line_breaks_count(content[-1], char)
                    content.extend(["\n"] * linebreak_amount)

                content.append(char)
            else:
                found_new_line = True

        return content

    def _get_box_boundaries(self, title_boundary: Boundary):
        left: float = 0.0
        right: float = 0.0

        assert self.text_align
        assert self.width_scale
        assert title_boundary.right
        assert title_boundary.left
        assert title_boundary.top
        assert title_boundary.bottom

        title_width: float = title_boundary.right - title_boundary.left

        if self.text_align == TextAlign.LEFT:
            left = title_boundary.left - self.increase_left
            right = title_boundary.left + (title_width * self.width_scale)

        if self.text_align == TextAlign.RIGHT:
            right = title_boundary.right + self.increase_right
            left = title_boundary.right - (title_width * self.width_scale)

        elif self.text_align == TextAlign.CENTER:
            title_center = title_boundary.left + (title_width / 2)
            half_box_width: float = (title_width * self.width_scale) / 2

            left = title_center - half_box_width
            right = title_center + half_box_width

        elif self.text_align == TextAlign.TO_THE_RIGHT:
            right = title_boundary.right + (title_width * self.width_scale)
            left = title_boundary.right

        top = title_boundary.top
        bottom = title_boundary.bottom - (self.char_height * self.height_scale)

        return Boundary(
            left=left,
            right=right,
            bottom=bottom,
            top=top,
            page_index=title_boundary.page_index,
        )

    class Config:
        arbitrary_types_allowed = True


class TextBox(TextBoxLayout):
    title: str | None = None
    box_characters: PDFPageChars = []
    content: str | None = None
    parent_name: str | None = None

    def load_content(self, pdf_pages_characters: list[PDFPageChars]) -> None:
        # Define title boundaries
        title_boundary: Boundary = self._get_title_boundaries(pdf_pages_characters)

        # Based one title's, define the box boundaries
        box_boundary: Boundary = self._get_box_boundaries(title_boundary)

        # Keep the filtered box to be used by children boxes
        self.box_characters: PDFPageChars = filter_pdf_characters(
            pdf_pages_characters, box_boundary
        )

        # Fix line breaks
        fixed_content: list[LTChar | str] = self._fix_line_breaks(self.box_characters)

        # Store the actual text content
        self.content = "".join(
            [
                cast(LTChar, c).get_text() if isinstance(c, LTChar) else c
                for c in fixed_content
            ]
        )

        # Load Children Boxes
        self.load_children()

    def load_children(self):
        for field in self.__fields__:
            instance = getattr(self, field)
            if isinstance(instance, TextBox):
                instance.height_scale = self.height_scale
                instance.parent_name = self.title
                instance.load_content([self.box_characters])

    def validate_content(self):
        if not self.content:
            raise ValueError(f"Not able to parse content from: {self}")

    @property
    def parsed_content(self) -> list[str]:
        self.validate_content()
        return self.content.split("\n")

    @property
    def raw_content(self) -> str:
        assert self.content
        return self.content

    def _get_title_boundaries(self, pdf_characters: list[PDFPageChars]) -> Boundary:
        matches = 0
        page_index = 0
        start_char: LTChar | None = None
        end_char: LTChar | None = None

        assert self.title, "Title must be set"

        for idx, pdf_page in enumerate(pdf_characters):
            page_index = idx
            for pdf_char in filter(lambda x: isinstance(x, LTChar), pdf_page):
                if pdf_char.get_text().lower() == self.title[matches].lower():
                    matches += 1
                    if matches == 1:
                        start_char = pdf_char
                    elif matches == len(self.title):
                        end_char = pdf_char
                        break
                else:
                    matches = 0
                    page_index = 0
                    start_char = None
                    end_char = None

            if start_char and end_char:
                break

        if not all([start_char, end_char]):
            raise ValueError(
                "Unable to find boundaries for title: "
                f"{self.parent_name  + ' -> ' if self.parent_name else ''}{self.title}'"
            )

        assert start_char
        assert end_char

        return Boundary(
            left=start_char.x0,
            right=end_char.x1,
            bottom=min(start_char.y0, end_char.y0),
            top=max(start_char.y1, end_char.y1),
            page_index=page_index,
        )


def filter_pdf_characters(
    pdf_characters: list[PDFPageChars], boundary: Boundary
) -> PDFPageChars:
    filtered_contents = pdf_characters[boundary.page_index]

    def filter_func(value):
        if not isinstance(value, LTChar):
            return True

        return all(
            [
                value.x0 >= boundary.left,
                value.x1 <= boundary.right,
                value.y1 <= boundary.top,
                value.y0 >= boundary.bottom,
            ]
        )

    filtered_contents = list(filter(filter_func, filtered_contents))

    while filtered_contents and isinstance(filtered_contents[0], LTAnno):
        del filtered_contents[0]

    while filtered_contents and isinstance(filtered_contents[-1], LTAnno):
        del filtered_contents[-1]

    return filtered_contents


def get_lines_between(start: str, end: str, pdf_lines: list[str]):
    start_re = re.compile(start)
    end_re = re.compile(end)
    start_idx: int | None = None
    end_idx: int | None = None

    for idx, line in enumerate(pdf_lines):
        if start_re.match(line):
            start_idx = idx
            continue

        if start_idx is not None and end_re.match(line):
            end_idx = idx
            break

    if start_idx is not None and end_idx is not None:
        return pdf_lines[start_idx + 1 : end_idx]

    return []
