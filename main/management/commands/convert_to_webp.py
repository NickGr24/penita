from django.core.management.base import BaseCommand
from django.conf import settings
from PIL import Image
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Convert all images in media and static/img directories to WebP format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quality',
            type=int,
            default=85,
            help='WebP quality (default: 85)',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip conversion if WebP file already exists',
        )

    def handle(self, *args, **options):
        quality = options['quality']
        skip_existing = options['skip_existing']

        # Directories to process
        media_root = Path(settings.MEDIA_ROOT)
        static_img = Path(settings.BASE_DIR) / 'main' / 'static' / 'img'

        directories = [media_root, static_img]

        total_converted = 0
        total_skipped = 0
        total_errors = 0

        for directory in directories:
            if not directory.exists():
                self.stdout.write(
                    self.style.WARNING(f'Directory {directory} does not exist, skipping...')
                )
                continue

            self.stdout.write(f'\nProcessing directory: {directory}')

            # Supported image formats
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

            for root, dirs, files in os.walk(directory):
                for filename in files:
                    file_path = Path(root) / filename
                    ext = file_path.suffix.lower()

                    if ext not in image_extensions:
                        continue

                    # Skip if already WebP
                    if ext == '.webp':
                        continue

                    # Create WebP filename
                    webp_path = file_path.with_suffix('.webp')

                    # Skip if WebP already exists and skip_existing is True
                    if skip_existing and webp_path.exists():
                        total_skipped += 1
                        continue

                    try:
                        # Open and convert image
                        with Image.open(file_path) as img:
                            # Convert RGBA to RGB if necessary
                            if img.mode in ('RGBA', 'LA', 'P'):
                                background = Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode == 'P':
                                    img = img.convert('RGBA')
                                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                                img = background

                            # Save as WebP
                            img.save(webp_path, 'WebP', quality=quality, method=6)

                        # Delete original file
                        file_path.unlink()

                        total_converted += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Converted: {file_path.relative_to(directory)} → {webp_path.name}')
                        )

                    except Exception as e:
                        total_errors += 1
                        self.stdout.write(
                            self.style.ERROR(f'✗ Error converting {file_path}: {str(e)}')
                        )

        # Update database records
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Updating database records...')
        self._update_database_records()

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Conversion complete!'))
        self.stdout.write(f'Total converted: {total_converted}')
        self.stdout.write(f'Total skipped: {total_skipped}')
        self.stdout.write(f'Total errors: {total_errors}')

    def _update_database_records(self):
        """Update database records to point to .webp files"""
        from main.models import News, NewsImage
        from books.models import Book

        updated_count = 0

        # Update News model
        for news in News.objects.all():
            if news.image and news.image.name:
                old_name = news.image.name
                if not old_name.endswith('.webp'):
                    # Replace extension with .webp
                    new_name = os.path.splitext(old_name)[0] + '.webp'
                    # Check if the webp file exists
                    webp_path = Path(settings.MEDIA_ROOT) / new_name
                    if webp_path.exists():
                        news.image.name = new_name
                        news.save(update_fields=['image'])
                        updated_count += 1
                        self.stdout.write(f'  Updated News: {news.title}')

        # Update NewsImage model
        for news_image in NewsImage.objects.all():
            if news_image.image and news_image.image.name:
                old_name = news_image.image.name
                if not old_name.endswith('.webp'):
                    new_name = os.path.splitext(old_name)[0] + '.webp'
                    webp_path = Path(settings.MEDIA_ROOT) / new_name
                    if webp_path.exists():
                        news_image.image.name = new_name
                        news_image.save(update_fields=['image'])
                        updated_count += 1
                        self.stdout.write(f'  Updated NewsImage for: {news_image.news.title}')

        self.stdout.write(self.style.SUCCESS(f'Database records updated: {updated_count}'))
