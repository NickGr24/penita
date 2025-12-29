from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
import os


def convert_to_webp(image_field, quality=85):
    """
    Convert an uploaded image to WebP format

    Args:
        image_field: Django ImageField or FileField instance
        quality: WebP quality (default: 85)

    Returns:
        InMemoryUploadedFile: WebP image file
    """
    if not image_field:
        return None

    # Get the uploaded file
    img_file = image_field

    # Skip if already WebP
    if img_file.name.lower().endswith('.webp'):
        return img_file

    try:
        # Open image
        img = Image.open(img_file)

        # Convert RGBA/LA/P to RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background

        # Create BytesIO object
        output = BytesIO()

        # Save as WebP
        img.save(output, format='WebP', quality=quality, method=6)
        output.seek(0)

        # Get original filename without extension
        original_name = os.path.splitext(img_file.name)[0]
        webp_name = f"{original_name}.webp"

        # Create InMemoryUploadedFile
        webp_file = InMemoryUploadedFile(
            output,
            'ImageField',
            webp_name,
            'image/webp',
            sys.getsizeof(output),
            None
        )

        return webp_file

    except Exception as e:
        print(f"Error converting image to WebP: {e}")
        return img_file  # Return original if conversion fails
