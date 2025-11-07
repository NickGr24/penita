import os
import django
from django.utils.text import slugify
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penita.settings')
django.setup()

from articles.models import Article
from books.models import Book
from main.models import News
from django.core.files.base import ContentFile
import io

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import simpleSplit
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    has_reportlab = True
except ImportError:
    has_reportlab = False
    print("ReportLab не установлен, будут созданы простые PDF файлы")

def create_test_pdf_simple(title, author, content):
    """Создание простого PDF файла с ReportLab"""
    buffer = io.BytesIO()
    
    if has_reportlab:
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Заголовок
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#333333'),
            spaceAfter=30
        )
        story.append(Paragraph(title, title_style))
        
        # Автор
        author_style = ParagraphStyle(
            'Author',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20
        )
        story.append(Paragraph(f"Autor: {author}", author_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Контент
        content_style = ParagraphStyle(
            'Content',
            parent=styles['Normal'],
            fontSize=12,
            leading=18,
            textColor=colors.HexColor('#333333')
        )
        
        # Разбиваем контент на параграфы
        for para in content.split('\n\n'):
            if para.strip():
                story.append(Paragraph(para.strip(), content_style))
                story.append(Spacer(1, 0.2*inch))
        
        doc.build(story)
    else:
        # Простой текстовый PDF без ReportLab
        buffer.write(f"{title}\n\n{author}\n\n{content}".encode('utf-8'))
    
    buffer.seek(0)
    return buffer

# Тестовые статьи (PDF формат)
articles_data = [
    {
        'name': 'Drepturile Fundamentale ale Omului',
        'description': 'Analiza completă a drepturilor fundamentale garantate prin Constituție și tratate internaționale.',
        'author': 'Tudor Osoianu',
        'category': 'procedura_penala',
        'content': '''Drepturile fundamentale ale omului reprezintă baza societății moderne democratice. 
        
Acestea sunt inalienabile și universale, aparținând fiecărei persoane indiferent de naționalitate, rasă sau religie.

Categorii principale:
- Drepturi civile și politice: dreptul la viață, libertatea de exprimare, dreptul la un proces echitabil
- Drepturi economice și sociale: dreptul la muncă, educație, sănătate  
- Drepturi culturale: dreptul la identitate culturală, participare la viața culturală

În Republica Moldova, drepturile fundamentale sunt garantate prin Constituție și prin tratatele internaționale ratificate. 
Curtea Constituțională veghează asupra respectării acestor drepturi.

"Demnitatea omului, drepturile și libertățile lui, libera dezvoltare a personalității umane, dreptatea și pluralismul politic reprezintă valori supreme și sunt garantate." - Art. 1 din Constituția RM

Cetățenii pot apela la multiple instituții pentru protecția drepturilor lor:
1. Avocatul Poporului (Ombudsman)
2. Instanțele de judecată naționale
3. Curtea Europeană a Drepturilor Omului'''
    },
    {
        'name': 'Procedura Penală în Republica Moldova',
        'description': 'Ghid complet al procesului penal cu explicarea fazelor și drepturilor părților.',
        'author': 'Dinu Ostavciuc',
        'category': 'criminalistica',
        'content': '''Procesul penal în Republica Moldova se bazează pe principii fundamentale care garantează un proces echitabil.

PREZUMȚIA DE NEVINOVĂȚIE
Orice persoană este considerată nevinovată până când vinovăția sa este dovedită în conformitate cu legea, printr-o sentință judecătorească definitivă.

DREPTUL LA APĂRARE
Fiecare persoană acuzată are următoarele drepturi:
- Să fie informată despre acuzațiile aduse
- Să aibă timp și facilități pentru pregătirea apărării
- Să se apere personal sau prin avocat
- Să solicite probe și să audieze martori

FAZELE PROCESULUI PENAL

1. Urmărirea penală - investigarea infracțiunii și strângerea probelor
2. Judecata - examinarea cauzei în instanță
3. Căile de atac - apel și recurs
4. Executarea - punerea în aplicare a hotărârii

Este esențial ca toate aceste faze să respecte garanțiile procedurale și drepturile fundamentale ale persoanei.

Orice încălcare a drepturilor procedurale poate duce la anularea actelor procesuale și chiar la achitarea inculpatului.'''
    },
    {
        'name': 'Contractele Civile - Ghid Practic',
        'description': 'Tot ce trebuie să știți despre încheierea și executarea contractelor civile.',
        'author': 'Tudor Osoianu',
        'category': 'alte_stiinte',
        'content': '''CONTRACTUL CIVIL - NOȚIUNI GENERALE

Contractul este acordul de voință dintre două sau mai multe părți, prin care se stabilesc, se modifică sau se sting raporturi juridice civile.

CONDIȚII DE VALIDITATE

Pentru a fi valid, un contract trebuie să îndeplinească:
1. Capacitatea părților - părțile trebuie să aibă capacitate deplină de exercițiu
2. Consimțământul - acordul de voință trebuie să fie liber și neviciat
3. Obiectul - trebuie să fie determinat și licit
4. Cauza - trebuie să fie licită și morală

TIPURI DE CONTRACTE FRECVENTE

• Contractul de vânzare-cumpărare - transferul proprietății contra unui preț
• Contractul de locațiune - folosința unui bun contra unei chirii
• Contractul de împrumut - remiterea unei sume de bani cu obligația de restituire
• Contractul de prestări servicii - executarea unor servicii contra remunerație

CLAUZE ESENȚIALE

Un contract bine redactat trebuie să conțină:
- Identificarea clară a părților
- Obiectul contractului precis definit
- Drepturile și obligațiile fiecărei părți
- Termene și modalități de executare
- Răspunderea pentru neexecutare
- Modalități de soluționare a litigiilor

Recomandare: Consultați întotdeauna un jurist înainte de semnarea contractelor importante!'''
    }
]

# Добавляем статьи
print("Adăugarea articolelor...")
for article_data in articles_data:
    article_slug = slugify(article_data['name'])
    article, created = Article.objects.get_or_create(
        slug=article_slug,
        defaults={
            'name': article_data['name'],
            'description': article_data['description'],
            'author': article_data['author'],
            'category': article_data['category'],
            'publication_date': datetime.now().date() - timedelta(days=random.randint(1, 30))
        }
    )
    
    if created:
        # Создаем PDF файл
        pdf_buffer = create_test_pdf_simple(
            article_data['name'],
            article_data['author'],
            article_data['content']
        )
        pdf_file = ContentFile(pdf_buffer.getvalue())
        article.file.save(f"{article_slug}.pdf", pdf_file)
        article.save()
        print(f"✓ Articol adăugat: {article.name}")
    else:
        print(f"• Articolul există deja: {article.name}")

# Тестовые новости
news_data = [
    {
        'title': 'Modificări importante în Codul Civil',
        'content': 'Parlamentul a adoptat astăzi modificări semnificative la Codul Civil, care vor intra în vigoare din 1 ianuarie 2025. Principalele schimbări vizează procedurile de moștenire și regimul matrimonial. Aceste modificări au fost mult așteptate de practicieni și vor simplifica semnificativ procedurile succesorale.',
    },
    {
        'title': 'Curtea Constituțională a declarat neconstituțională legea X',
        'content': 'În ședința de astăzi, Curtea Constituțională a declarat neconstituțională legea privind impozitarea suplimentară, considerând că aceasta încalcă principiul egalității în fața legii. Decizia a fost luată cu majoritate de voturi și va avea efecte imediate asupra sistemului fiscal.',
    },
    {
        'title': 'Seminar gratuit despre drepturile consumatorilor',
        'content': 'Penița Dreptului organizează un seminar gratuit despre drepturile consumatorilor în era digitală. Evenimentul va avea loc pe 15 decembrie 2024, ora 14:00. Participarea este gratuită, însă numărul de locuri este limitat. Înscrieri la contact@penitadreptului.md',
    },
    {
        'title': 'Noua lege a protecției datelor personale',
        'content': 'A intrat în vigoare noua lege privind protecția datelor cu caracter personal, armonizată cu GDPR. Toate companiile au obligația să se conformeze noilor cerințe în termen de 6 luni. Nerespectarea prevederilor poate duce la amenzi de până la 4% din cifra de afaceri.',
    }
]

# Добавляем новости
print("\nAdăugarea știrilor...")
for news_item in news_data:
    news_slug = slugify(news_item['title'])
    news, created = News.objects.get_or_create(
        slug=news_slug,
        defaults={
            'title': news_item['title'],
            'content': news_item['content'],
        }
    )
    if created:
        print(f"✓ Știre adăugată: {news.title}")
    else:
        print(f"• Știrea există deja: {news.title}")

# Тестовые книги
books_data = [
    {
        'title': 'Ghidul Juridic al Cetățeanului',
        'description': 'O carte completă despre drepturile și obligațiile cetățenilor în Republica Moldova. Include explicații detaliate ale procedurilor juridice comune și sfaturi practice pentru situații cotidiene.',
        'author': 'Tudor Osoianu',
        'content': '''GHIDUL JURIDIC AL CETĂȚEANULUI

INTRODUCERE
Această carte este destinată tuturor cetățenilor care doresc să înțeleagă mai bine sistemul juridic și drepturile lor fundamentale.

CAPITOLUL 1: DREPTURILE FUNDAMENTALE
Fiecare cetățean are drepturi garantate prin Constituție. Acestea includ dreptul la viață, libertate, proprietate și acces la justiție.

Drepturile civile și politice:
- Dreptul la viață și integritate fizică
- Libertatea de exprimare și opinie
- Dreptul de vot și de a fi ales
- Libertatea de circulație

CAPITOLUL 2: OBLIGAȚIILE CIVICE
Respectarea legilor și participarea la viața societății sunt obligații fundamentale ale fiecărui cetățean.

Principalele obligații:
- Plata impozitelor și taxelor
- Respectarea drepturilor celorlalți
- Participarea la apărarea țării
- Protejarea mediului înconjurător

CAPITOLUL 3: PROCEDURI ADMINISTRATIVE
Cum să interacționați eficient cu instituțiile publice:
- Redactarea cererilor și petițiilor
- Termene și proceduri
- Căi de atac administrative
- Răspunderea funcționarilor

CAPITOLUL 4: PROTECȚIA JURIDICĂ
Căi de atac și remedii legale disponibile:
- Acțiunea în instanță
- Asistența juridică gratuită
- Medierea și arbitrajul
- Executarea hotărârilor judecătorești

CONCLUZII
Cunoașterea drepturilor și obligațiilor este esențială pentru o societate democratică funcțională.'''
    },
    {
        'title': 'Drept Penal pentru Toți',
        'description': 'Explicații clare și accesibile ale sistemului de justiție penală, destinate publicului larg. Cartea demitizează conceptele juridice complexe.',
        'author': 'Dinu Ostavciuc',
        'content': '''DREPT PENAL PENTRU TOȚI

PREFAȚĂ
Această lucrare își propune să facă accesibil dreptul penal pentru persoanele fără studii juridice.

PARTEA I: INTRODUCERE ÎN DREPTUL PENAL

Ce este o infracțiune?
Infracțiunea este fapta prevăzută de legea penală, săvârșită cu vinovăție, nejustificată și imputabilă persoanei care a săvârșit-o.

Elementele infracțiunii:
1. Subiectul - persoana care săvârșește infracțiunea
2. Latura obiectivă - fapta propriu-zisă
3. Obiectul - valoarea socială protejată
4. Latura subiectivă - vinovăția (intenție sau culpă)

PARTEA II: PRINCIPIILE FUNDAMENTALE

Prezumția de nevinovăție
Orice persoană este considerată nevinovată până la dovedirea vinovăției prin hotărâre definitivă.

Legalitatea incriminării și pedepsei
Nimeni nu poate fi condamnat pentru o faptă care nu era prevăzută de lege la momentul săvârșirii.

PARTEA III: PROCEDURA PENALĂ PAS CU PAS

1. Sesizarea organelor de urmărire penală
2. Începerea urmăririi penale
3. Efectuarea urmăririi penale
4. Trimiterea în judecată
5. Judecata în primă instanță
6. Căile de atac
7. Executarea pedepsei

PARTEA IV: DREPTURILE VICTIMELOR

Protecție și compensații disponibile:
- Dreptul la protecție fizică
- Asistență juridică gratuită
- Compensații financiare
- Măsuri de protecție a martorilor'''
    },
    {
        'title': 'Manual de Drept Civil',
        'description': 'Manual comprehensiv de drept civil, acoperind contracte, proprietate, familie și succesiuni. Ideal pentru studenți și practicieni.',
        'author': 'Tudor Osoianu, Dinu Ostavciuc',
        'content': '''MANUAL DE DREPT CIVIL

INTRODUCERE GENERALĂ
Dreptul civil reprezintă ramura fundamentală a dreptului privat, reglementând raporturile patrimoniale și nepatrimoniale dintre persoane fizice și juridice.

PARTEA I: TEORIA GENERALĂ

Capitolul 1: Persoanele
Persoana fizică - capacitatea de folosință și capacitatea de exercițiu
Persoana juridică - constituire, funcționare, dizolvare

Capitolul 2: Bunurile
Clasificarea bunurilor
Drepturile reale principale și accesorii
Posesia și proprietatea

Capitolul 3: Actul juridic civil
Condiții de validitate
Nulitatea actului juridic
Modalitățile actului juridic

PARTEA II: OBLIGAȚII ȘI CONTRACTE

Capitolul 1: Teoria generală a obligațiilor
Izvoarele obligațiilor
Efectele obligațiilor
Transmisiunea și stingerea obligațiilor

Capitolul 2: Contracte speciale
Vânzarea-cumpărarea
Donația
Locațiunea
Împrumutul
Mandatul

PARTEA III: DREPTUL FAMILIEI

Capitolul 1: Căsătoria
Condițiile încheierii căsătoriei
Drepturile și obligațiile soților
Regimurile matrimoniale

Capitolul 2: Divorțul
Cauzele divorțului
Procedura divorțului
Efectele divorțului

PARTEA IV: SUCCESIUNI

Capitolul 1: Moștenirea legală
Clasele de moștenitori
Reprezentarea succesorală
Calculul cotelor succesorale

Capitolul 2: Moștenirea testamentară
Formele testamentului
Capacitatea de a testa
Dezmoștenirea'''
    }
]

# Добавляем книги
print("\nAdăugarea cărților...")
for book_data in books_data:
    book_slug = slugify(book_data['title'])
    book, created = Book.objects.get_or_create(
        slug=book_slug,
        defaults={
            'title': book_data['title'],
            'description': book_data['description'],
            'author': book_data['author'],
        }
    )
    
    if created:
        # Создаем PDF файл
        pdf_buffer = create_test_pdf_simple(
            book_data['title'],
            book_data['author'],
            book_data['content']
        )
        pdf_file = ContentFile(pdf_buffer.getvalue())
        book.file.save(f"{book_slug}.pdf", pdf_file)
        book.save()
        print(f"✓ Carte adăugată: {book.title}")
    else:
        print(f"• Cartea există deja: {book.title}")

# Статистика
print("\n" + "="*50)
print("✅ Date de test adăugate cu succes!")
print("="*50)
print(f"📄 Articole totale: {Article.objects.count()}")
print(f"📰 Știri totale: {News.objects.count()}")
print(f"📚 Cărți totale: {Book.objects.count()}")
print("="*50)