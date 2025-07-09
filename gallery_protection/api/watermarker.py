from PIL import Image, ImageDraw, ImageFont
import io
import os
import frappe

def add_watermark(image_path: str, text: str = "amanksolutions.com") -> bytes:
    original_image = Image.open(image_path)
    original_format = original_image.format
    image = original_image.convert("RGBA")
    width, height = image.size

    watermark_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark_layer)

    # Load DejaVu font or fallback
    try:
        font_path = os.path.join(
            frappe.get_app_path('gallery_protection'), 'Michroma-Regular.ttf'
        )
        font = ImageFont.truetype(font_path, 40)
    except IOError:
        font = ImageFont.load_default()    # Get size of text to space correctly

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # x_spacing = text_width + 100
    # y_spacing = 250

    # for y in range(0, height, y_spacing):
    #     row_offset = ((y // y_spacing) % 2) * (x_spacing // 2)
    #     for x in range(-text_width, width + text_width, x_spacing):
    #         draw.text((x + row_offset, y), text, font=font, fill=(150, 150, 150, 50))

    draw.text((50, height//2), text, font=font, fill=(50, 50, 50, 255))
    draw.text(((width-text_width)-50, height//2), text, font=font, fill=(50, 50, 50, 50))

    # Combine and convert to RGB
    combined = Image.alpha_composite(image, watermark_layer).convert("RGB")

    buffer = io.BytesIO()
    combined.save(buffer, format=original_format)
    return buffer.getvalue()

def add_watermark_half(image_path: str, text: str = "amanksolutions.com") -> bytes:
    original_image = Image.open(image_path)
    original_format = original_image.format
    image = original_image.convert("RGBA")
    width, height = image.size

    watermark_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark_layer)

    # Load DejaVu font or fallback
    try:
        font_path = os.path.join(
            frappe.get_app_path('gallery_protection'), 'Michroma-Regular.ttf'
        )
        font = ImageFont.truetype(font_path, 40)
    except IOError:
        font = ImageFont.load_default()    # Get size of text to space correctly

    # Get size of text to space correctly
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # x_spacing = text_width + 100
    # y_spacing = 250

    # for y in range(0, height, y_spacing):
    #     row_offset = ((y // y_spacing) % 2) * (x_spacing // 2)
    #     for x in range(-text_width, width + text_width, x_spacing):
    #         draw.text((x + row_offset, y), text, font=font, fill=(150, 150, 150, 50))

    # draw.text((50, height//2), text, font=font, fill=(50, 50, 50, 50))
    draw.text((width//2 - text_width//2, height//2), text, font=font, fill=(50, 50, 50, 50))

    # Combine and convert to RGB
    combined = Image.alpha_composite(image, watermark_layer).convert("RGB")

    buffer = io.BytesIO()
    combined.save(buffer, format=original_format)
    return buffer.getvalue()
