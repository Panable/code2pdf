from pygments import highlight
from pygments.lexers import guess_lexer_for_filename
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from pypdf import PdfMerger

import pdfkit
import sys

import pathlib


from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def create_pdf_with_string(text, filename):
    filename = filename+".pdf"

    font_size = 36

    # Create a canvas with A4 page size
    c = canvas.Canvas(filename, pagesize=A4)

    # Set font size
    c.setFont("Helvetica", font_size)

    # Get text width and height
    text_width = c.stringWidth(text)
    text_height = font_size

    # Get page width and height
    page_width, page_height = A4

    # Calculate position to center text
    x = (page_width - text_width) / 2
    y = (page_height - text_height) / 2

    # Draw the text on the canvas
    c.drawString(x, y, text)

    # Save the PDF
    c.save()
    return filename


def gen_pdf(filename, filepath, pdfs, style='monokai'):
    try:
        with open(filepath, 'rb') as file:
            code = file.read()

        # Guess the lexer for the given file name
        lexer = guess_lexer_for_filename(filepath, code)

        # Highlight the code using the guessed lexer and custom style
        highlighted_code = highlight(code, lexer, HtmlFormatter(style=style))

        # Get CSS styles for the highlighted code
        css_styles = HtmlFormatter(style=style).get_style_defs('.highlight')

        opts = {
            'page-size': 'A4',
            'margin-top': '0mm',
            'margin-right': '0mm',
            'margin-bottom': '0mm',
            'margin-left': '0mm',
        }

        # Generate HTML content
        html_content = f"<style>{css_styles}</style>{highlighted_code}"

        filename = filename.replace(".", "")

        filepathparts = filepath.split('/')

        last_three_parts = ''.join(filepathparts[-3:])

        output_filename = 'res/'+last_three_parts+".pdf"

        print(output_filename)

        # Convert HTML to PDF
        pdfkit.from_string(html_content, output_filename, options=opts)
    except ClassNotFound:
        print("Error: Unsupported file type")

    pdfs.append(filepath)


def append_subdir(name, path, pdfs):
    html_files = list(path.rglob('*' + '.html'))
    css_files = list(path.rglob('*' + '.css'))
    js_files = list(path.rglob('*' + '.js'))

    pdfs.append(create_pdf_with_string(name, 'res/'+name+"Heading"))

    for file in html_files:
        gen_pdf(file.name, str(file), pdfs)
    for file in css_files:
        gen_pdf(file.name, str(file), pdfs)
    for file in js_files:
        gen_pdf(file.name, str(file), pdfs)


def highlight_code_to_pdf(rootdir, style='default'):

    pdfs = []

    if rootdir.startswith('~'):
        rootdir = str(pathlib.Path.home()) + rootdir[1:]

    children_dirs = list(pathlib.Path(rootdir).iterdir())

    children_dirs = sorted(children_dirs)
    children_dirs = [dir for dir in children_dirs if dir.is_dir(
    ) and not dir.name.endswith('.git')]

    for child in children_dirs:
        parts = child.parts
        print("name is" + child.name)
        name = ''.join(parts[-3:])
        append_subdir(name, child, pdfs)

    merger = PdfMerger()

    for pdf in pdfs:
        merger.append(pdf)

    merger.write("result.pdf")
    merger.close()


# Example usage
if __name__ == "__main__":
    filename = "hello.c"

    if len(sys.argv) == 1:
        print("[ERROR] Specify file input")
        exit(1)

    filename = sys.argv[1]

    custom_style = 'monokai'  # Specify your custom style here
    highlight_code_to_pdf(filename, style=custom_style)
