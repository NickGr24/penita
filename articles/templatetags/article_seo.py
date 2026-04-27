import re

from django import template

register = template.Library()


_GARBAGE_PATTERNS = [
    re.compile(r'(?i)\bCZU[:\s]*[\d\.\(\)/:]+'),
    re.compile(r'(?i)\bDOI[:\s]*\S+'),
    re.compile(r'(?i)\bISSN[\s-]*\d{4}-?\d{4}'),
    re.compile(r'(?i)\bzenodo\.\d+'),
    re.compile(r'(?i)https?://\S+'),
    re.compile(r'(?i)\bnr\.\s*\d+\s*\(\s*\d+\s*\)\s*[,/]?\s*\d{4}'),
    re.compile(r'(?i)pag(?:ina)?[\.\s]*\d+'),
    re.compile(
        r'(?i)(?:'
        r'LEGEA\s+[ȘŞ]I\s+VIA[ȚŢ]A'
        r'|REVISTA\s+INSTITUTULUI(?:\s+NA[ȚŢ]IONAL)?(?:\s+AL\s+JUSTI[ȚŢ]IEI)?'
        r'|STUDII\s+NA[ȚŢ]IONALE\s+DE\s+SECURITATE'
        r'|[ȘŞ]tiin[țţ]e\s+juridice(?://\s*Legal\s+Sciences)?'
        r'|Materialele\s+conferin[țţ]ei[^,.]*'
        r'|Studii\s+[șş]i\s+comentarii'
        r'|Publica[țţ]ie\s+[ștşşt]+iin[țţ]ifico-?practic[ăa]?'
        r'|edi[țţ]ie\s+special[ăa]'
        r'|SESIUNEA[^,.]*'
        r'|mai-iunie|martie\s*-\s*aprilie|noiembrie-decembrie'
        # Word-boundary версия — обязательные пробелы между токенами + concrete окончания.
        # Это matches только split-PDF "Jurispru de nță" (с пробелами), НЕ "jurisprudenței".
        r'|Jurispru\s+de\s+n[țţ](?:[ăa])?(?=\s|$)'
        r')\s*'
    ),
    re.compile(r'\b(?:ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie)\s+\d{4}', re.IGNORECASE),
]

_LEADING_NOISE = re.compile(r'^[\s\d\.\-—:,;()\[\]/]+')


@register.filter(name='clean_seo_description')
def clean_seo_description(text, min_length=60):
    """
    Чистит description от типичного "мусора" PDF-метаданных
    (CZU, ISSN, DOI, заголовки журналов, даты выпусков).
    Если после чистки осталось меньше min_length символов —
    возвращает пустую строку (фолбэк делает шаблон).
    """
    if not text:
        return ''
    cleaned = str(text)
    for pattern in _GARBAGE_PATTERNS:
        cleaned = pattern.sub(' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = _LEADING_NOISE.sub('', cleaned).strip()
    try:
        min_length = int(min_length)
    except (TypeError, ValueError):
        min_length = 60
    if len(cleaned) < min_length:
        return ''
    return cleaned


@register.filter(name='truncate_meta')
def truncate_meta(text, max_length=160):
    """
    Обрезает text по словам в пределах max_length символов и добавляет '…'.
    Используется для meta description / og:description — лучше чем
    truncatechars (который рвёт слова) и truncatewords (который не
    учитывает символьный лимит, важный для SERP-сниппетов).
    """
    if not text:
        return ''
    text = str(text).strip()
    try:
        max_length = int(max_length)
    except (TypeError, ValueError):
        max_length = 160
    if len(text) <= max_length:
        return text
    # Резервируем 1 символ под '…'
    cut = text[:max_length - 1]
    last_space = cut.rfind(' ')
    if last_space > max_length // 2:
        cut = cut[:last_space]
    return cut.rstrip(' ,.;:!?-—') + '…'
