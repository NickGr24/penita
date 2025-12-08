import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penita.settings')
sys.path.append('/home/nikita/Desktop/penita')
django.setup()

from books.models import Book
from payments.models import MAIBSettings

def setup_book_prices():
    """Set up sample prices for existing books"""
    
    # Define books and their prices
    book_prices = {
        'Căile de atac în procesul penal': 150.00,  # Paid book
        'Procedurile Standard': 0.00,  # Free book
        'Reținerea persoanei de către poliție': 200.00,  # Paid book
        'Drept penal pentru toți': 0.00,  # Free book
        'Ghidul juridic al cetățeanului': 100.00,  # Paid book
        'Manual de drept civil': 250.00,  # Paid book
    }
    
    print("Setting up book prices...")
    
    for title, price in book_prices.items():
        try:
            book = Book.objects.get(title=title)
            book.price = price
            book.save()  # is_paid will be set automatically based on price
            
            status = "PAID" if book.is_paid else "FREE"
            print(f"  {title}: {price} MDL ({status})")
        except Book.DoesNotExist:
            print(f"  Book '{title}' not found")
    
    print("\nBook prices updated successfully!")
    
    # Display summary
    paid_books = Book.objects.filter(is_paid=True)
    free_books = Book.objects.filter(is_paid=False)
    
    print(f"\nSummary:")
    print(f"  Total books: {Book.objects.count()}")
    print(f"  Paid books: {paid_books.count()}")
    print(f"  Free books: {free_books.count()}")
    
    if paid_books.exists():
        print("\nPaid books:")
        for book in paid_books:
            print(f"  - {book.title}: {book.price} MDL")

def setup_maib_test_config():
    """Create MAIB test configuration"""
    
    # Check if test config already exists
    if MAIBSettings.objects.filter(mode='test').exists():
        print("\nMAIB test configuration already exists")
        config = MAIBSettings.objects.get(mode='test')
        print(f"  Mode: {config.mode}")
        print(f"  Active: {config.is_active}")
        print(f"  API URL: {config.api_base_url}")
        print("\n  Note: Update Project ID, Secret, and Signature Key in admin panel")
    else:
        # Create test configuration
        config = MAIBSettings.objects.create(
            mode='test',
            project_id='YOUR_TEST_PROJECT_ID',
            project_secret='YOUR_TEST_PROJECT_SECRET',
            signature_key='YOUR_TEST_SIGNATURE_KEY',
            api_base_url='https://api.maibmerchants.md/v1',
            is_active=True
        )
        print("\nMAIB test configuration created!")
        print("  IMPORTANT: Update the following in admin panel:")
        print("  1. Project ID")
        print("  2. Project Secret")
        print("  3. Signature Key")
        print("  These will be provided by MAIB for your test project")

if __name__ == '__main__':
    setup_book_prices()
    setup_maib_test_config()
    
    print("\n" + "="*50)
    print("Setup complete!")
    print("\nNext steps:")
    print("1. Go to admin panel (/admin) and update MAIB Settings with your test credentials")
    print("2. Test the payment flow with a paid book")
    print("3. Use MAIB test cards for testing:")
    print("   - Success: 4111 1111 1111 1111")
    print("   - Failure: 4000 0000 0000 0002")
    print("\nAdmin login: admin / admin123")