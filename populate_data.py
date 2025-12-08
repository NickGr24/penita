import os
import sys
import django
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penita.settings')
sys.path.append('/home/nikita/Desktop/penita')
django.setup()

from django.contrib.auth.models import User
from books.models import Book, Subscription, PromoCode
from articles.models import Article
from main.models import News
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone as dj_timezone

def create_superuser():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Superuser 'admin' created with password 'admin123'")
    else:
        print("Superuser 'admin' already exists")

def populate_books():
    book_files = [
        ('Caile-de-atac-in-procesul-penal.pdf', 'Căile de atac în procesul penal', 
         'Ghid comprehensive despre căile de atac în procesul penal din Moldova', 'Tudor Osoianu'),
        ('procedurile_standard_ro.pdf', 'Procedurile Standard', 
         'Manual despre procedurile standard în sistemul juridic', 'Dinu Ostavciuc'),
        ('retinerea_persoanei_de_catre_politie._concluziile_unei_cercetari.pdf', 
         'Reținerea persoanei de către poliție', 
         'Studiu despre drepturile și procedurile în cazul reținerii de către poliție', 
         'Tudor Osoianu, Dinu Ostavciuc'),
        ('drept-penal-pentru-toti.pdf', 'Drept penal pentru toți',
         'Introducere în dreptul penal accesibilă pentru publicul larg', 'Tudor Osoianu'),
        ('ghidul-juridic-al-cetateanului.pdf', 'Ghidul juridic al cetățeanului',
         'Ghid practic pentru cetățeni despre drepturile și obligațiile lor', 'Dinu Ostavciuc'),
        ('manual-de-drept-civil.pdf', 'Manual de drept civil',
         'Manual comprehensiv de drept civil pentru studenți și practicieni', 'Tudor Osoianu, Dinu Ostavciuc')
    ]
    
    print("\nPopulating books...")
    books_created = 0
    
    for filename, title, description, author in book_files:
        file_path = Path('media/books') / filename
        
        if not Book.objects.filter(title=title).exists():
            if file_path.exists():
                try:
                    book = Book.objects.create(
                        title=title,
                        description=description,
                        author=author,
                        file=f'books/{filename}'
                    )
                    books_created += 1
                    print(f"  Created book: {title}")
                except Exception as e:
                    print(f"  Error creating book {title}: {e}")
            else:
                print(f"  File not found: {file_path}")
        else:
            print(f"  Book already exists: {title}")
    
    print(f"Created {books_created} books")

def populate_articles():
    articles_data = [
        ('Procedura penală modernă', 'Analiză a noilor modificări în codul de procedură penală', 
         'procedura_penala', 'Tudor Osoianu'),
        ('Tehnici criminalistice avansate', 'Studiu despre metodele moderne de investigație criminalistică',
         'criminalistica', 'Dinu Ostavciuc'),
        ('Dreptul european și impactul său', 'Analiza impactului legislației europene asupra sistemului juridic moldovenesc',
         'alte_stiinte', 'Tudor Osoianu, Dinu Ostavciuc'),
        ('Garanții procesuale în procesul penal', 'Studiu despre drepturile și garanțiile acuzatului',
         'procedura_penala', 'Tudor Osoianu'),
        ('ADN-ul ca probă în proces', 'Utilizarea probelor ADN în investigațiile criminalistice',
         'criminalistica', 'Dinu Ostavciuc'),
    ]
    
    print("\nPopulating articles...")
    articles_created = 0
    
    for name, description, category, author in articles_data:
        if not Article.objects.filter(name=name).exists():
            try:
                dummy_file = SimpleUploadedFile(
                    f"{name.lower().replace(' ', '_')}.pdf",
                    b"Dummy PDF content for article",
                    content_type="application/pdf"
                )
                
                article = Article.objects.create(
                    name=name,
                    description=description,
                    category=category,
                    author=author,
                    file=dummy_file
                )
                articles_created += 1
                print(f"  Created article: {name}")
            except Exception as e:
                print(f"  Error creating article {name}: {e}")
        else:
            print(f"  Article already exists: {name}")
    
    print(f"Created {articles_created} articles")

def populate_news():
    news_data = [
        ('Conferință internațională de drept',
         'Universitatea de Stat din Moldova a organizat o conferință internațională despre dezvoltările recente în dreptul penal european.',
         'conducere_doctorate.JPG'),
        ('Premiul Constantin Stere acordat',
         'Profesorul Tudor Osoianu a primit prestigiosul Premiu Constantin Stere pentru contribuțiile sale în domeniul științelor juridice.',
         'Premiul_Constantin_Stere.webp'),
        ('Lansare nouă platformă juridică online',
         'A fost lansată o nouă platformă digitală pentru accesul cetățenilor la informații juridice și consultanță legală.',
         'Screenshot_from_2024-12-11_16-01-23.webp'),
    ]
    
    print("\nPopulating news...")
    news_created = 0
    
    for title, content, image_file in news_data:
        if not News.objects.filter(title=title).exists():
            image_path = Path('media/news') / image_file
            
            if image_path.exists():
                try:
                    news = News.objects.create(
                        title=title,
                        content=content,
                        image=f'news/{image_file}'
                    )
                    news_created += 1
                    print(f"  Created news: {title}")
                except Exception as e:
                    print(f"  Error creating news {title}: {e}")
            else:
                print(f"  Image file not found: {image_path}")
        else:
            print(f"  News already exists: {title}")
    
    print(f"Created {news_created} news items")

def create_sample_subscriptions():
    print("\nCreating sample subscriptions and promo codes...")
    
    # Create test users
    test_users = [
        ('user1', 'user1@example.com', 'password123'),
        ('user2', 'user2@example.com', 'password123'),
    ]
    
    for username, email, password in test_users:
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username=username, email=email, password=password)
            print(f"  Created user: {username}")
            
            # Create subscription for first user
            if username == 'user1':
                Subscription.objects.create(
                    user=user,
                    plan='monthly',
                    start_date=dj_timezone.now()
                )
                print(f"    Added monthly subscription for {username}")
    
    # Create promo codes
    promo_codes = [
        ('WELCOME2024', 20),
        ('STUDENT50', 50),
        ('EARLYBIRD', 30),
    ]
    
    for code, discount in promo_codes:
        if not PromoCode.objects.filter(code=code).exists():
            PromoCode.objects.create(
                code=code,
                discount_percentage=discount,
                is_active=True,
                expiration_date=dj_timezone.now() + dj_timezone.timedelta(days=90)
            )
            print(f"  Created promo code: {code} ({discount}% discount)")

def main():
    print("Starting database population...")
    print("=" * 50)
    
    create_superuser()
    populate_books()
    populate_articles()
    populate_news()
    create_sample_subscriptions()
    
    print("\n" + "=" * 50)
    print("Database population completed!")
    print("\nSummary:")
    print(f"  Books: {Book.objects.count()}")
    print(f"  Articles: {Article.objects.count()}")
    print(f"  News: {News.objects.count()}")
    print(f"  Users: {User.objects.count()}")
    print(f"  Subscriptions: {Subscription.objects.count()}")
    print(f"  Promo Codes: {PromoCode.objects.count()}")
    
    print("\nYou can now log in to the admin panel with:")
    print("  Username: admin")
    print("  Password: admin123")

if __name__ == '__main__':
    main()