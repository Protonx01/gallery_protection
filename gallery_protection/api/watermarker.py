from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import os
import frappe

def add_watermark(image_path: str, wmark_path: str = "amanksolutions.png") -> bytes:
    original_image = Image.open(image_path)
    original_format = original_image.format
    image = original_image.convert("RGBA")
    width, height = image.size

    resample_filter = getattr(Image, 'Resampling', Image).LANCZOS

    # draw = ImageDraw.Draw(watermark_layer)

    # Load DejaVu font or fallback
    try:
        wmark_full_path = os.path.join(
            frappe.get_app_path('gallery_protection'), wmark_path
        )
        watermark = Image.open(wmark_full_path)
    except IOError:
        watermark = ""
        print(f"image not found at {wmark_full_path}")    

    watermark_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))

    # bbox = draw.textbbox((0, 0), text, font=font)
    # text_width = bbox[2] - bbox[0]
    # text_height = bbox[3] - bbox[1]

    # draw.text((50, height//2), text, font=font, fill=(50, 50, 50, 50))
    # draw.text(((width-text_width)-50, height//2), text, font=font, fill=(50, 50, 50, 50))



    # Resize watermark (optional)
    scale = 1.05
    new_width = int(width * scale)
    w_percent = new_width / float(watermark.size[0])
    new_height = int((float(watermark.size[1]) * w_percent))
    watermark = watermark.resize((new_width, new_height), resample_filter)
    watermark = watermark.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))


    # Vertical center
    y_pos = (height - new_height) // 2


    # Paste watermark on both left and right 
    left_pos = (0, 0)
    # right_pos = (width - new_width - 50, y_pos)

    watermark_layer.paste(watermark, left_pos, watermark)
    #watermark_layer.paste(watermark, right_pos, watermark)

    # Combine and convert to RGB
    combined = Image.alpha_composite(image, watermark_layer).convert("RGB")

    buffer = io.BytesIO()
    combined.save(buffer, format=original_format)
    return buffer.getvalue()

def add_watermark_half(image_path: str, wmark_path: str = "amanksolutions.png") -> bytes:
    original_image = Image.open(image_path)
    original_format = original_image.format
    image = original_image.convert("RGBA")
    width, height = image.size
    resample_filter = getattr(Image, 'Resampling', Image).LANCZOS

    # draw = ImageDraw.Draw(watermark_layer)

    # Load DejaVu font or fallback
    try:
        wmark_full_path = os.path.join(
            frappe.get_app_path('gallery_protection'), wmark_path
        )
        watermark = Image.open(wmark_full_path)
    except IOError:
        watermark = ""
        print(f"image not found at {wmark_full_path}")    

    watermark_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    
    # bbox = draw.textbbox((0, 0), text, font=font)
    # text_width = bbox[2] - bbox[0]
    # text_height = bbox[3] - bbox[1]

    # draw.text((50, height//2), text, font=font, fill=(50, 50, 50, 50))
    # draw.text(((width-text_width)-50, height//2), text, font=font, fill=(50, 50, 50, 50))



    # Resize watermark (optional)
    scale = 1.05
    new_width = int(width * scale)
    w_percent = new_width / float(watermark.size[0])
    new_height = int((float(watermark.size[1]) * w_percent))
    watermark = watermark.resize((new_width, new_height), resample_filter)
    watermark = watermark.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))


    # Vertical center
    y_pos = (height - new_height) // 2


    # Paste watermark on both left and right 
    left_pos = (-10, y_pos//2 + 50)
    # right_pos = (width - new_width - 50, y_pos)

    watermark_layer.paste(watermark, left_pos, watermark)
    #watermark_layer.paste(watermark, right_pos, watermark)

    # Combine and convert to RGB
    combined = Image.alpha_composite(image, watermark_layer).convert("RGB")

    buffer = io.BytesIO()
    combined.save(buffer, format=original_format)
    return buffer.getvalue()
