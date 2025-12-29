from django.core.management.base import BaseCommand
from django.conf import settings
from rembg import remove
from PIL import Image
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Remove background from specified images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help='Specific file or directory path to process',
        )
        parser.add_argument(
            '--pattern',
            type=str,
            help='File pattern to match (e.g., "osoianu,ostavciuc")',
        )

    def handle(self, *args, **options):
        path = options.get('path')
        pattern = options.get('pattern')

        if path:
            # Process specific path
            target_path = Path(path)
            if target_path.is_file():
                self._process_file(target_path)
            elif target_path.is_dir():
                self._process_directory(target_path, pattern)
        else:
            # Default: process author images
            static_img = Path(settings.BASE_DIR) / 'main' / 'static' / 'img'
            self._process_directory(static_img, pattern or 'osoianu,ostavciuc')

    def _process_directory(self, directory, pattern=None):
        """Process all images in directory, optionally filtered by pattern"""
        if not directory.exists():
            self.stdout.write(
                self.style.WARNING(f'Directory {directory} does not exist')
            )
            return

        self.stdout.write(f'\nProcessing directory: {directory}')

        patterns = pattern.split(',') if pattern else []
        total_processed = 0

        for file_path in directory.glob('*.webp'):
            # Filter by pattern if specified
            if patterns:
                if not any(p.strip().lower() in file_path.name.lower() for p in patterns):
                    continue

            if self._process_file(file_path):
                total_processed += 1

        self.stdout.write(
            self.style.SUCCESS(f'\nTotal images processed: {total_processed}')
        )

    def _process_file(self, file_path):
        """Remove background from a single image file"""
        try:
            self.stdout.write(f'Processing: {file_path.name}...')

            # Open image
            with Image.open(file_path) as img:
                # Remove background
                output = remove(img)

                # Save with transparency
                output.save(file_path, 'WebP', quality=95, method=6)

            self.stdout.write(
                self.style.SUCCESS(f'✓ Background removed: {file_path.name}')
            )
            return True

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error processing {file_path.name}: {str(e)}')
            )
            return False
