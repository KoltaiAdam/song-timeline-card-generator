import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
import hashlib
import argparse
import textwrap

pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBlack', 'ariblk.ttf'))

def generate_qr_code(url, file_path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=0,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(file_path)

def add_qr_code_with_border(c, url, position, box_size, padding_size=110):
    hash_object = hashlib.sha256(url.encode())
    hex_dig = hash_object.hexdigest()

    qr_code_path = f"qr_{hex_dig}.png"  # Unique path for each QR code
    background_path = "background_inverted.png"
    generate_qr_code(url, qr_code_path)
    x, y = position
    c.setStrokeColorRGB(255,255,255) 
    c.setFillColorRGB(0,0,0)
    c.drawImage(background_path, x, y, width=box_size, height=box_size)
    c.drawImage(qr_code_path, x+(padding_size/2), y+(padding_size/2), width=box_size-padding_size, height=box_size-padding_size)
    c.rect(x, y, box_size, box_size, 1, 0)

def add_text_box(c, info, position, box_size, small_font_size=18, big_font_size=44):
    x, y = position
    text_margin = 30
    small_font_type = "Arial"
    big_font_type = "ArialBlack"

    c.setFont(small_font_type, small_font_size)
    artist_text = f"{info['Artist']}"
    title_text = f"{info['Title']}"
    year_text = f"{info['Year']}"
    tier_text = f"{info['Tier']}"
    if tier_text == "1":
        tier_text = "°"
    else:
        tier_text = "° °"

    print(f"Artist:{artist_text}" + "  " + f"Title: {title_text} " + " " + f"Year: {year_text}")
    # Calculate the centered position for each line of text
    
    artist_x = x + (box_size - c.stringWidth(artist_text, small_font_type, small_font_size)) / 2
    title_x = x + (box_size - c.stringWidth(title_text, small_font_type, small_font_size)) / 2
    year_x = x + (box_size - c.stringWidth(year_text, big_font_type, big_font_size)) / 2
    tier_x = x + (box_size - c.stringWidth(tier_text, small_font_type, small_font_size)) / 2

    # Split the text into multiple lines if it doesn't fit in the width
    artist_lines = textwrap.wrap(artist_text, width=int(len(artist_text) / c.stringWidth(artist_text, small_font_type, small_font_size) * (box_size - text_margin)))
    title_lines = textwrap.wrap(title_text, width=int(len(title_text) / c.stringWidth(title_text, small_font_type, small_font_size) * (box_size - text_margin)))

    # Calculate the centered position for each line of text
    artist_y = y + box_size - (small_font_size *2) + 5
    title_y = y + (len(title_lines) * small_font_size) + 10
    year_y = y + (box_size / 2) - (big_font_size / 2) + 10
    tier_y = y + 5

    #number of artist lines
    artist_lines_count = len(artist_lines)
    title_lines_count = len(title_lines)

    if artist_lines_count == 1:
        artist_y = artist_y - (small_font_size / 2)
    if artist_lines_count == 3:
        artist_y = artist_y + (small_font_size / 2)

    if title_lines_count == 1:
        title_y = title_y + (small_font_size / 2)
    if title_lines_count == 3:
        title_y = title_y - (small_font_size / 2) + 3

    # Draw each line of text
    for line in artist_lines:
        artist_x = x + (box_size - c.stringWidth(line, small_font_type, small_font_size)) / 2
        c.drawString(artist_x, artist_y, line)
        artist_y -= small_font_size + 2

    for line in title_lines:
        title_x = x + (box_size - c.stringWidth(line, small_font_type, small_font_size)) / 2
        c.drawString(title_x, title_y, line)
        title_y -= small_font_size + 2

    c.drawString(tier_x, tier_y, tier_text)
    c.setFont(big_font_type, big_font_size)
    c.drawString(year_x, year_y, year_text)
    c.setStrokeColorRGB(0.95,0.95,0.95) 
    c.rect(x, y, box_size, box_size, 1, 0)

def main(csv_file_path, output_pdf_path):
    data = pd.read_csv(csv_file_path, sep=";")
    data = data.map(lambda x: x.strip() if isinstance(x, str) else x)


    c = canvas.Canvas(output_pdf_path, pagesize=A4)
    page_width, page_height = A4
    box_size = 6.5 * cm
    boxes_per_row = int(page_width // box_size)
    boxes_per_column = int(page_height // box_size)
    boxes_per_page = boxes_per_row * boxes_per_column
    vpageindent = 0.8 * cm
    hpageindent = (page_width - (box_size * boxes_per_row)) / 2

    for i in range(0, len(data), boxes_per_page):
        # write to console the progress
        print(f"Processing {i} of {len(data)}")
    # Generate QR codes
        for index in range(i, min(i + boxes_per_page, len(data))):
            row = data.iloc[index]
            position_index = index % (boxes_per_row * boxes_per_column)
            column_index = position_index % boxes_per_row
            row_index = position_index // boxes_per_row
            x = hpageindent + (column_index * box_size)
            y = page_height - vpageindent - (row_index + 1) * box_size
            add_qr_code_with_border(c, row['URL'], (x, y), box_size)

        c.showPage()

        # Add text information
        for index in range(i, min(i + boxes_per_page, len(data))):
            row = data.iloc[index]
            position_index = index % boxes_per_page
            column_index = (boxes_per_row-1) - position_index % boxes_per_row
            row_index = position_index // boxes_per_row
            x = hpageindent + (column_index * box_size)
            y = page_height - vpageindent - (row_index + 1) * box_size
            add_text_box(c, row, (x, y), box_size)

        c.showPage()

    c.save()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", help="Path to the CSV file")
    parser.add_argument("output_pdf", help="Path to the output PDF file")
    args = parser.parse_args()

    main(args.csv_file, args.output_pdf)
