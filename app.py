from flask import Flask, request, render_template, redirect, url_for, send_file
import os
import fitz  # PyMuPDF
from prettytable import PrettyTable
import imgkit
from io import BytesIO
import tempfile
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'files/'

def rgb_to_normalized(rgb):
    """Convert RGB values from 0-255 to 0-1 range."""
    return tuple(c / 255.0 for c in rgb)

def is_color_match(color, target_color, tolerance=0.1):
    """Check if the color matches the target color within a tolerance."""
    return all(abs(c - t) < tolerance for c, t in zip(color, target_color))

def extract_rgb_from_int(color_int):
    """Convert an integer color value to an RGB tuple."""
    # Convert to unsigned int
    color_int = color_int & 0xFFFFFFFF
    # Extract RGB values
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return (r, g, b)

def extract_questions_answers(page):
    text_instances = page.get_text("dict")["blocks"]
    questions = []
    answers = []
    question_fonts = []  # Store fonts for questions
    answer_fonts = []    # Store fonts for answers
    
    # Define the target colors in normalized format
    red_color = rgb_to_normalized((255, 0, 0))  # RED (for questions)
    green_color = rgb_to_normalized((0, 176, 80))  # GREEN (for answers)
    
    current_answers = []  # Temporary storage for answers
    current_answer_fonts = []  # Temporary storage for answer fonts
    question_found = False  # Tracks whether we are inside a question

    for block in text_instances:
        if "lines" in block:  # Check if the block contains text
            for line in block["lines"]:
                for span in line["spans"]:
                    rgb_color = extract_rgb_from_int(span["color"])  # Convert color
                    text_content = span['text'].strip().replace(".", "")  # Get the text content
                    font_name = span['font'].split(",")[0]  # Get the actual font name excluding bold
                    
                    # Check if it's a question (red-colored text)
                    if is_color_match(rgb_to_normalized(rgb_color), red_color) and text_content:
                        # Store the last question's answer(s) before starting a new question
                        if question_found:
                            answers.append(" + ".join(current_answers) if current_answers else "Blank")
                            answer_fonts.append(current_answer_fonts[0] if current_answer_fonts else "Arial")  # Use first answer font
                            current_answers = []
                            current_answer_fonts = []
                        
                        questions.append(text_content)
                        question_fonts.append(font_name)
                        question_found = True
                    
                    # Check if it's an answer (green-colored text)
                    elif is_color_match(rgb_to_normalized(rgb_color), green_color) and text_content:
                        current_answers.append(text_content)
                        current_answer_fonts.append(font_name)

    # Ensure the last collected answers are added
    if question_found:
        answers.append(" + ".join(current_answers) if current_answers else "Blank")
        answer_fonts.append(current_answer_fonts[0] if current_answer_fonts else "Times-Roman")

    return questions, answers, question_fonts, answer_fonts


def change_text_color_in_pdf(page, doc):
    # Change all non-black colors to black
        for xref in page.get_contents():
            stream = doc.xref_stream(xref)
            if stream:
                # Split the stream into parts
                parts = stream.split(b' rg')  # 'rg' is the PDF command for setting RGB color
                
                new_stream = b''
                for i, part in enumerate(parts):
                    if i < len(parts) - 1:  # All parts except the last one
                        # Check if this part ends with color values (3 numbers)
                        color_start = part.rfind(b'\n')  # Find the last newline
                        if color_start == -1:
                            color_start = 0
                        
                        # Take everything before the color values
                        new_stream += part[:color_start] + b'\n0 0 0'
                        new_stream += b' rg'  # Add back the color command
                    else:
                        new_stream += part  # Add the last part as is
                
                doc.update_stream(xref, stream.replace(b' RG', b' rg').replace(b'0 0 0 rg', b'0 0 0 rg'))
                doc.update_stream(xref, new_stream)

def generate_html_table(questions, answers, question_fonts, answer_fonts):
    # Generate HTML table string with white background and fonts
    img = "<img src='https://i.ibb.co.com/rG75b3BD/image-white-bg.png' style='width:100px; height:100px; object-fit:cover' />"
    table = "<table border='1' style='border-collapse: collapse; font-size: 20px; max-width: 20px; margin: 0; padding: 0; background-color: transparent;'>"
    table += f"<thead><tr style='padding-bottom: 7px; border: none;'><th>{img}</th></tr>"
    
    for i, (q, a, q_font, a_font) in enumerate(zip(questions, answers, question_fonts, answer_fonts)):
        # Combine question and answer with their respective fonts
        cell_content = f"<span style='font-family: \"{q_font}\"'>{q}.</span>"
        cell_content += f"<span style='font-family: \"{a_font}\"; margin-left: 5px;'>{a}.</span>"
        
        table += f"<tr><td style='padding: 7px;'>{cell_content}</td></tr>"
    
    table += "</thead></tbody></table>"
    
    return table

def html_to_image(html):
    """Converts HTML to a tightly cropped image."""
    options = {
        "format": "png",
        "quality": 100,
        "disable-smart-width": "",
        "transparent": "",
        "crop-w": "130"  # Force crop to specific width (adjust based on your table)
    }

    # Convert HTML to image
    img_bytes = imgkit.from_string(html, False, options=options)

    # Load image and crop aggressively
    image = Image.open(BytesIO(img_bytes)).convert("RGBA")
    
    # Use getbbox() to detect content boundaries and crop whitespace
    bbox = image.getbbox()
    if bbox:
        cropped_image = image.crop(bbox)
    else:
        cropped_image = image  # Fallback if cropping fails

    # Save to stream
    image_stream = BytesIO()
    cropped_image.save(image_stream, format="PNG")
    image_stream.seek(0)

    return image_stream, cropped_image.width

def insert_image_into_pdf_footer(doc, image_stream, page, content_width):
    """Inserts the image into the footer with proper scaling."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
        temp_img.write(image_stream.getvalue())
        temp_img_path = temp_img.name

    image = Image.open(temp_img_path)
    img_width, img_height = image.size

    # Scale image to fit desired width in PDF (e.g., 200 units)
    desired_width = 43  # Adjust this based on your PDF layout
    scale_factor = desired_width / img_width
    new_width = desired_width
    new_height = int(img_height * scale_factor)

    # Position calculations
    page_width = page.rect.width
    page_height = page.rect.height
    margin_bottom = 50  # Space from bottom

    # Adjust for even/odd pages
    if page.number % 2 == 0:
        left = page_width - new_width - 24  # Right-aligned
    else:
        left = 20  # Left-aligned

    rect = fitz.Rect(
        left,
        page_height - margin_bottom - new_height,  # Top
        left + new_width,  # Right
        page_height - margin_bottom  # Bottom
    )

    page.insert_image(rect, filename=temp_img_path)
    # os.remove(temp_img_path)

def process_pdf(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    
    for page in doc:
        questions, answers, question_fonts, answer_fonts = extract_questions_answers(page)
        
        # Convert all text to black
        change_text_color_in_pdf(page, doc)
        
        if questions and answers:
            html_table = generate_html_table(questions, answers, question_fonts, answer_fonts)
            print(html_table)

            # Get the image and its actual content width
            image_stream, content_width = html_to_image(html_table)
            insert_image_into_pdf_footer(doc, image_stream, page, content_width)
    
    # Save after all insertions are done
    doc.save(output_pdf)
    print(f"Saved modified PDF to: {output_pdf}")
    doc.close()

@app.route('/')
def upload_form():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        return redirect(request.url)
    
    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        # Call the PDF processing function here
        output_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output.pdf')
        process_pdf(file_path, output_pdf_path)  # Now defined

        # Send the file from the output folder
        return send_file(
            output_pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=file.filename
        )
        
        # return f'File processed successfully! <a href="{output_pdf_path}">Download Output PDF</a>'
    
    return 'Invalid file format. Please upload a PDF file.'

if __name__ == '__main__':
    app.run(debug=True)