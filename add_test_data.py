import os
import sys
import django
from django.utils.text import slugify
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penita.settings')
django.setup()

from articles.models import Article
from books.models import Book
from main.models import News
from django.contrib.auth.models import User

# Создаем суперпользователя если его нет
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@example.com',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created:
    admin_user.set_password('admin123')
    admin_user.save()
    print("Создан суперпользователь admin")

# Тестовые статьи
articles_data = [
    {
        'title': 'Drepturile Fundamentale ale Omului',
        'content': '''<h2>Introducere în drepturile omului</h2>
        <p>Drepturile fundamentale ale omului reprezintă baza societății moderne democratice. Acestea sunt inalienabile și universale, aparținând fiecărei persoane indiferent de naționalitate, rasă sau religie.</p>
        
        <h3>Categorii principale</h3>
        <ul>
            <li><strong>Drepturi civile și politice</strong> - dreptul la viață, libertatea de exprimare, dreptul la un proces echitabil</li>
            <li><strong>Drepturi economice și sociale</strong> - dreptul la muncă, educație, sănătate</li>
            <li><strong>Drepturi culturale</strong> - dreptul la identitate culturală, participare la viața culturală</li>
        </ul>
        
        <h3>Protecția juridică</h3>
        <p>În Republica Moldova, drepturile fundamentale sunt garantate prin Constituție și prin tratatele internaționale ratificate. Curtea Constituțională veghează asupra respectării acestor drepturi.</p>
        
        <blockquote>"Demnitatea omului, drepturile și libertățile lui, libera dezvoltare a personalității umane, dreptatea și pluralismul politic reprezintă valori supreme și sunt garantate." - Art. 1 din Constituția RM</blockquote>
        
        <h3>Mecanisme de apărare</h3>
        <p>Cetățenii pot apela la multiple instituții pentru protecția drepturilor lor:</p>
        <ol>
            <li>Avocatul Poporului (Ombudsman)</li>
            <li>Instanțele de judecată naționale</li>
            <li>Curtea Europeană a Drepturilor Omului</li>
        </ol>''',
        'author': 'Tudor Osoianu',
        'category': 'Drept Constitutional',
    },
    {
        'title': 'Procedura Penală în Republica Moldova',
        'content': '''<h2>Principiile procedurii penale</h2>
        <p>Procesul penal în Republica Moldova se bazează pe principii fundamentale care garantează un proces echitabil și protecția drepturilor tuturor părților implicate.</p>
        
        <h3>Prezumția de nevinovăție</h3>
        <p>Orice persoană este considerată nevinovată până când vinovăția sa este dovedită în conformitate cu legea, printr-o sentință judecătorească definitivă. Acest principiu este consacrat atât în Constituție, cât și în Codul de procedură penală.</p>
        
        <h3>Dreptul la apărare</h3>
        <p>Fiecare persoană acuzată are dreptul:</p>
        <ul>
            <li>Să fie informată despre acuzațiile aduse</li>
            <li>Să aibă timp și facilități pentru pregătirea apărării</li>
            <li>Să se apere personal sau prin avocat</li>
            <li>Să solicite probe și să audieze martori</li>
        </ul>
        
        <h3>Fazele procesului penal</h3>
        <ol>
            <li><strong>Urmărirea penală</strong> - investigarea infracțiunii și strângerea probelor</li>
            <li><strong>Judecata</strong> - examinarea cauzei în instanță</li>
            <li><strong>Căile de atac</strong> - apel și recurs</li>
            <li><strong>Executarea</strong> - punerea în aplicare a hotărârii</li>
        </ol>
        
        <p>Este esențial ca toate aceste faze să respecte garanțiile procedurale și drepturile fundamentale ale persoanei.</p>''',
        'author': 'Dinu Ostavciuc',
        'category': 'Drept Penal',
    },
    {
        'title': 'Contractele Civile: Ghid Practic',
        'content': '''<h2>Noțiuni generale despre contracte</h2>
        <p>Contractul este acordul de voință dintre două sau mai multe părți, prin care se stabilesc, se modifică sau se sting raporturi juridice civile.</p>
        
        <h3>Condiții de validitate</h3>
        <p>Pentru a fi valid, un contract trebuie să îndeplinească următoarele condiții:</p>
        <ul>
            <li><strong>Capacitatea părților</strong> - părțile trebuie să aibă capacitate deplină de exercițiu</li>
            <li><strong>Consimțământul</strong> - acordul de voință trebuie să fie liber și neviciat</li>
            <li><strong>Obiectul</strong> - trebuie să fie determinat și licit</li>
            <li><strong>Cauza</strong> - trebuie să fie licită și morală</li>
        </ul>
        
        <h3>Tipuri de contracte frecvente</h3>
        <ol>
            <li><strong>Contractul de vânzare-cumpărare</strong> - transferul proprietății contra unui preț</li>
            <li><strong>Contractul de locațiune</strong> - folosința unui bun contra unei chirii</li>
            <li><strong>Contractul de împrumut</strong> - remiterea unei sume de bani cu obligația de restituire</li>
            <li><strong>Contractul de prestări servicii</strong> - executarea unor servicii contra remunerație</li>
        </ol>
        
        <h3>Clauze esențiale</h3>
        <p>Un contract bine redactat trebuie să conțină:</p>
        <ul>
            <li>Identificarea clară a părților</li>
            <li>Obiectul contractului precis definit</li>
            <li>Drepturile și obligațiile fiecărei părți</li>
            <li>Termene și modalități de executare</li>
            <li>Răspunderea pentru neexecutare</li>
            <li>Modalități de soluționare a litigiilor</li>
        </ul>''',
        'author': 'Tudor Osoianu',
        'category': 'Drept Civil',
    },
    {
        'title': 'Protecția Consumatorului în Era Digitală',
        'content': '''<h2>Drepturile consumatorilor online</h2>
        <p>Comerțul electronic a adus noi provocări în protecția consumatorilor, dar și noi drepturi și garanții specifice mediului digital.</p>
        
        <h3>Informarea precontractuală</h3>
        <p>Înainte de încheierea contractului online, consumatorul trebuie informat despre:</p>
        <ul>
            <li>Identitatea completă a comerciantului</li>
            <li>Caracteristicile esențiale ale produsului sau serviciului</li>
            <li>Prețul total, inclusiv taxe și costuri de livrare</li>
            <li>Dreptul de retragere din contract</li>
            <li>Durata contractului și condițiile de reziliere</li>
        </ul>
        
        <h3>Dreptul de retragere</h3>
        <p>Consumatorul are dreptul să se retragă din contractul la distanță în termen de 14 zile calendaristice, fără a fi nevoit să justifice decizia de retragere și fără a suporta alte costuri decât cele de returnare a produsului.</p>
        
        <h3>Protecția datelor personale</h3>
        <p>În contextul GDPR și legislației naționale:</p>
        <ol>
            <li>Consimțământul explicit pentru procesarea datelor</li>
            <li>Dreptul la informare despre utilizarea datelor</li>
            <li>Dreptul la ștergerea datelor ("dreptul de a fi uitat")</li>
            <li>Dreptul la portabilitatea datelor</li>
        </ol>
        
        <h3>Soluționarea litigiilor</h3>
        <p>Consumatorii au la dispoziție mai multe căi:</p>
        <ul>
            <li>Reclamație directă la comerciant</li>
            <li>Agenția pentru Protecția Consumatorilor</li>
            <li>Platforma europeană de soluționare online a litigiilor</li>
            <li>Instanțele de judecată</li>
        </ul>''',
        'author': 'Dinu Ostavciuc',
        'category': 'Drept Commercial',
    },
    {
        'title': 'Răspunderea Medicală: Aspecte Juridice',
        'content': '''<h2>Cadrul legal al răspunderii medicale</h2>
        <p>Răspunderea medicală reprezintă obligația personalului medical de a răspunde pentru prejudiciile cauzate pacienților în exercitarea profesiei.</p>
        
        <h3>Tipuri de răspundere</h3>
        <ul>
            <li><strong>Răspunderea civilă</strong> - obligația de a repara prejudiciul cauzat</li>
            <li><strong>Răspunderea penală</strong> - pentru infracțiuni în exercitarea profesiei</li>
            <li><strong>Răspunderea disciplinară</strong> - pentru încălcarea normelor deontologice</li>
        </ul>
        
        <h3>Condiții pentru angajarea răspunderii</h3>
        <ol>
            <li>Existența unei fapte ilicite (eroare medicală)</li>
            <li>Producerea unui prejudiciu</li>
            <li>Legătura de cauzalitate între faptă și prejudiciu</li>
            <li>Vinovăția medicului</li>
        </ol>
        
        <h3>Drepturile pacientului</h3>
        <p>Pacientul are dreptul la:</p>
        <ul>
            <li>Informare completă despre diagnostic și tratament</li>
            <li>Consimțământ informat pentru orice intervenție</li>
            <li>Confidențialitatea datelor medicale</li>
            <li>Acces la dosarul medical</li>
            <li>Compensații în caz de malpraxis</li>
        </ul>
        
        <h3>Prevenirea litigiilor medicale</h3>
        <p>Măsuri esențiale pentru personalul medical:</p>
        <ul>
            <li>Documentarea completă a actului medical</li>
            <li>Obținerea consimțământului scris</li>
            <li>Comunicare eficientă cu pacientul</li>
            <li>Respectarea protocoalelor medicale</li>
            <li>Asigurare de malpraxis adecvată</li>
        </ul>''',
        'author': 'Tudor Osoianu',
        'category': 'Drept Medical',
    }
]

# Добавляем статьи
for article_data in articles_data:
    article, created = Article.objects.get_or_create(
        slug=slugify(article_data['title']),
        defaults={
            'title': article_data['title'],
            'content': article_data['content'],
            'author': article_data['author'],
            'category': article_data['category'],
            'published_date': datetime.now() - timedelta(days=random.randint(1, 30))
        }
    )
    if created:
        print(f"Добавлена статья: {article.title}")
    else:
        print(f"Статья уже существует: {article.title}")

# Тестовые новости
news_data = [
    {
        'title': 'Modificări importante în Codul Civil',
        'content': 'Parlamentul a adoptat astăzi modificări semnificative la Codul Civil, care vor intra în vigoare din 1 ianuarie 2025. Principalele schimbări vizează procedurile de moștenire și regimul matrimonial.',
        'image': None,
    },
    {
        'title': 'Curtea Constituțională a declarat neconstituțională legea X',
        'content': 'În ședința de astăzi, Curtea Constituțională a declarat neconstituțională legea privind impozitarea suplimentară, considerând că aceasta încalcă principiul egalității în fața legii.',
        'image': None,
    },
    {
        'title': 'Seminar gratuit despre drepturile consumatorilor',
        'content': 'Penița Dreptului organizează un seminar gratuit despre drepturile consumatorilor în era digitală. Evenimentul va avea loc pe 15 decembrie 2024, ora 14:00.',
        'image': None,
    }
]

# Добавляем новости
for news_item in news_data:
    news, created = News.objects.get_or_create(
        slug=slugify(news_item['title']),
        defaults={
            'title': news_item['title'],
            'content': news_item['content'],
            'image': news_item['image'],
            'published_date': datetime.now() - timedelta(days=random.randint(1, 10))
        }
    )
    if created:
        print(f"Добавлена новость: {news.title}")
    else:
        print(f"Новость уже существует: {news.title}")

# Создаем тестовые PDF файлы для книг
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.files.base import ContentFile

def create_test_pdf(title, author, content):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Заголовок
    p.setFont("Helvetica-Bold", 24)
    p.drawString(100, 750, title)
    
    # Автор
    p.setFont("Helvetica", 14)
    p.drawString(100, 720, f"Autor: {author}")
    
    # Содержание
    p.setFont("Helvetica", 12)
    y = 680
    for line in content.split('\n'):
        if y < 50:
            p.showPage()
            y = 750
        p.drawString(100, y, line[:80])
        y -= 20
    
    p.save()
    buffer.seek(0)
    return buffer

# Тестовые книги
books_data = [
    {
        'title': 'Ghidul Juridic al Cetățeanului',
        'description': 'O carte completă despre drepturile și obligațiile cetățenilor în Republica Moldova. Include explicații detaliate ale procedurilor juridice comune și sfaturi practice pentru situații cotidiene.',
        'author': 'Tudor Osoianu',
        'content': '''Capitolul 1: Drepturile fundamentale
Fiecare cetățean are drepturi garantate prin Constituție...

Capitolul 2: Obligațiile civice
Respectarea legilor și participarea la viața societății...

Capitolul 3: Proceduri administrative
Cum să interacționați cu instituțiile publice...

Capitolul 4: Protecția juridică
Căi de atac și remedii legale disponibile...'''
    },
    {
        'title': 'Drept Penal pentru Toți',
        'description': 'Explicații clare și accesibile ale sistemului de justiție penală, destinate publicului larg. Cartea demitizează conceptele juridice complexe.',
        'author': 'Dinu Ostavciuc',
        'content': '''Introducere în dreptul penal
Ce este o infracțiune și cum se clasifică...

Principiile fundamentale
Prezumția de nevinovăție și alte garanții...

Procedura penală pas cu pas
De la sesizare până la sentință...

Drepturile victimelor
Protecție și compensații disponibile...'''
    },
    {
        'title': 'Manual de Drept Civil',
        'description': 'Manual comprehensiv de drept civil, acoperind contracte, proprietate, familie și succesiuni. Ideal pentru studenți și practicieni.',
        'author': 'Tudor Osoianu, Dinu Ostavciuc',
        'content': '''Partea I: Teoria generală
Persoane, bunuri și acte juridice...

Partea II: Obligații și contracte
Formarea și executarea contractelor...

Partea III: Dreptul familiei
Căsătoria, divorțul și relațiile de familie...

Partea IV: Succesiuni
Moștenirea legală și testamentară...'''
    }
]

# Добавляем книги
for book_data in books_data:
    book, created = Book.objects.get_or_create(
        slug=slugify(book_data['title']),
        defaults={
            'title': book_data['title'],
            'description': book_data['description'],
            'author': book_data['author'],
        }
    )
    
    if created:
        # Создаем PDF файл
        pdf_buffer = create_test_pdf(
            book_data['title'],
            book_data['author'],
            book_data['content']
        )
        pdf_file = ContentFile(pdf_buffer.getvalue())
        book.file.save(f"{slugify(book_data['title'])}.pdf", pdf_file)
        book.save()
        print(f"Добавлена книга: {book.title}")
    else:
        print(f"Книга уже существует: {book.title}")

print("\n✅ Тестовые данные успешно добавлены!")
print(f"Статей: {Article.objects.count()}")
print(f"Новостей: {News.objects.count()}")
print(f"Книг: {Book.objects.count()}")