import os
import re
import pdfplumber
from django.core.management.base import BaseCommand
from articles.models import Article


class Command(BaseCommand):
    help = 'Извлекает текст из PDF файлов статей и заполняет seo_content и excerpt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Перезаписать существующий seo_content',
        )
        parser.add_argument(
            '--slug',
            type=str,
            help='Обработать только конкретную статью по slug',
        )

    def handle(self, *args, **options):
        force = options['force']
        slug = options.get('slug')

        articles = Article.objects.all()
        if slug:
            articles = articles.filter(slug=slug)

        total = articles.count()
        success = 0
        skipped = 0
        failed = 0

        for article in articles:
            if article.seo_content and not force:
                self.stdout.write(f'  SKIP: {article.name} (already has content)')
                skipped += 1
                continue

            if not article.file:
                self.stdout.write(self.style.WARNING(f'  NO FILE: {article.name}'))
                failed += 1
                continue

            file_path = article.file.path
            if not os.path.exists(file_path):
                self.stdout.write(self.style.WARNING(f'  MISSING: {file_path}'))
                failed += 1
                continue

            if not file_path.lower().endswith('.pdf'):
                self.stdout.write(self.style.WARNING(f'  NOT PDF: {file_path}'))
                failed += 1
                continue

            try:
                text = self._extract_text(file_path)
                if not text or len(text.strip()) < 50:
                    self.stdout.write(self.style.WARNING(
                        f'  LOW TEXT: {article.name} ({len(text.strip())} chars)'))
                    failed += 1
                    continue

                # Clean and format text
                clean_text = self._clean_text(text)
                
                # Convert to simple HTML paragraphs
                html_content = self._text_to_html(clean_text)
                
                # Generate excerpt (first ~400 chars)
                excerpt = self._make_excerpt(clean_text, max_len=450)

                article.seo_content = html_content
                if not article.excerpt or force:
                    article.excerpt = excerpt
                article.save(update_fields=['seo_content', 'excerpt'])

                self.stdout.write(self.style.SUCCESS(
                    f'  OK: {article.name} ({len(html_content)} chars)'))
                success += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'  ERROR: {article.name} - {e}'))
                failed += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done: {success} extracted, {skipped} skipped, {failed} failed out of {total}'))

    def _extract_text(self, pdf_path):
        """Extract all text from PDF using pdfplumber."""
        full_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
        return '\n\n'.join(full_text)

    def _clean_text(self, text):
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        # Remove page numbers (standalone numbers on lines)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        # Normalize line breaks - join lines that are part of the same paragraph
        lines = text.split('\n')
        paragraphs = []
        current = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current:
                    paragraphs.append(' '.join(current))
                    current = []
            else:
                current.append(line)
        
        if current:
            paragraphs.append(' '.join(current))
        
        return '\n\n'.join(paragraphs)

    def _text_to_html(self, text):
        """Convert clean text to HTML paragraphs."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        html_parts = []
        for p in paragraphs:
            # Escape HTML
            p = p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_parts.append(f'<p>{p}</p>')
        return '\n'.join(html_parts)

    def _make_excerpt(self, text, max_len=450):
        """Create a short excerpt from the text."""
        # Take first paragraph(s) up to max_len
        text = text.replace('\n\n', ' ').replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) <= max_len:
            return text
        # Cut at last sentence boundary
        cut = text[:max_len]
        last_period = cut.rfind('.')
        if last_period > max_len // 2:
            return cut[:last_period + 1]
        return cut[:max_len].rsplit(' ', 1)[0] + '...'
