from pygments import highlight
from pygments.lexers import guess_lexer_for_filename
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

import pdfkit
import sys

import pathlib

import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer


from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

import asyncio
from pyppeteer import launch

from PyPDF2 import PdfFileMerger


def create_pdf_with_string(text, pdfs):
    filename = f"res/{len(pdfs)}.pdf"

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
    pdfs.append(filename)


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

        output_filename = f"res/{len(pdfs)}.pdf"

        print(output_filename)

        # Convert HTML to PDF
        pdfkit.from_string(html_content, output_filename, options=opts)
    except ClassNotFound:
        print("Error: Unsupported file type")

    pdfs.append(output_filename)


async def delay(time):
    await asyncio.sleep(time / 1000)  # Convert milliseconds to seconds


async def gen_webpages(html_files, servepath, pdfs):
    browser = await launch(executablePath="/usr/bin/google-chrome-stable")
    page = await browser.newPage()

    root_url = "http://0.0.0.0:8000/"
    for file in html_files:

        filename = f"res/{len(pdfs)}.pdf"
        relative_server_url = str(file).replace(str(servepath), '')
        url = root_url + relative_server_url

        await page.goto(url)

        # Add a delay of 5 seconds (adjust as needed)
        await delay(4)

        await page.pdf({'path': filename, 'format': 'A4'})

        pdfs.append(filename)

        await browser.close()


async def append_subdir(dirName, path, pdfs, servepath=''):
    html_files = list(path.rglob('*' + '.html'))
    css_files = list(path.rglob('*' + '.css'))
    js_files = list(path.rglob('*' + '.js'))

    create_pdf_with_string(dirName, pdfs)
    for file in html_files:
        gen_pdf(file.name, str(file), pdfs)
    for file in css_files:
        gen_pdf(file.name, str(file), pdfs)
    for file in js_files:
        gen_pdf(file.name, str(file), pdfs)

    print("generating webpage...")
    await gen_webpages(html_files, servepath, pdfs)
    print("page generated.")


async def highlight_code_to_pdf(rootdir, style='default'):

    pdfs = []

    if rootdir.startswith('~'):
        rootdir = str(pathlib.Path.home()) + rootdir[1:]

    children_dirs = list(pathlib.Path(rootdir).iterdir())

    children_dirs = sorted(children_dirs)
    children_dirs = [dir for dir in children_dirs if dir.is_dir(
    ) and not dir.name.endswith('.git')]

    for child in children_dirs:
        await append_subdir(child.name, child, pdfs, rootdir)

    merge(pdfs)


def merge(pdfs):
    print(pdfs)
    output_path = 'output.pdf'
    print("merging")
    merger = PdfFileMerger()

    for path in pdfs:
        try:
            merger.append(path)
        except Exception as e:
            print(f"Failed to merge file: {path}. Error: {e}")

    merger.write(output_path)
    merger.close()


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Headers',
                         'X-Requested-With, Content-Type')
        SimpleHTTPRequestHandler.end_headers(self)


def get_server(port, directory):
    server_address = ('', port)

    handler = lambda *args, **kwargs: CORSRequestHandler(
        *args, directory=directory, **kwargs)

    print(f'Starting server on port {port}, serving directory {directory}...')
    httpd = SignalingHTTPServer(server_address, handler)
    return httpd


def run_server(server):
    server.serve_forever()


def translate_path(self, path):
    if path.startswith('~'):
        path = str(pathlib.Path.home()) + path[1:]

    # Get the absolute path of the directory to serve
    root = pathlib.Path(self.directory).resolve()
    # Combine the absolute path with the requested path
    path = pathlib.Path(path).expanduser().resolve()
    if path.is_relative_to(root):
        return str(path)
    else:
        return str(root / '404.html')


class SignalingHTTPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ready_event = threading.Event()

    def service_actions(self):
        super().service_actions()
        self.ready_event.set()


# Example usage
if __name__ == "__main__":
    filename = "hello.c"

    if len(sys.argv) == 1:
        print("[ERROR] Specify file input")
        exit(1)

    filename = sys.argv[1]

    port = 8000

    server = get_server(port, filename)

    # Start the server in a separate thread
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server.ready_event.wait()

    asyncio.get_event_loop().run_until_complete(
        highlight_code_to_pdf(filename, 'monokai'))

    # Shutdown the server

    server.shutdown()
