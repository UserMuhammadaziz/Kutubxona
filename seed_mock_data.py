#!/usr/bin/env python
"""
Comprehensive mock data generator for Kutubxona stress testing.
Creates:
- 50+ books with various genres
- 100+ copies (nusxa)
- 30+ students (oquvchi) 
- 5 librarians (kutubxonachi)
- Active loans, overdue loans, reservations
- Fines (jarima)
"""
import os
import sys
import random
from datetime import timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.timezone import now

from kitob.models import Kitob
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi, Ariza
from berish.models import Berish
from navbat.models import Navbat
from jarima.models import Jarima

User = get_user_model()

# Sample data
BOOKS = [
    ("O'tkan kunlar", "Abdulla Qodiriy", "badiiy", 1926, "G'afur G'ulom"),
    ("Mehrobdan chayon", "Abdulla Qodiriy", "badiiy", 1929, "G'afur G'ulom"),
    ("Sarob", "O'tkir Hoshimov", "badiiy", 1985, "Sharq"),
    ("Ikki eshik orasi", "O'tkir Hoshimov", "badiiy", 1994, "Sharq"),
    ("Kecha va kunduz", "Abdulla Qahhor", "badiiy", 1935, "Yosh gvardiya"),
    ("Ufq", "Cholpon", "badiiy", 1922, "Turon"),
    ("Tunggi odam", "Tohir Malik", "badiiy", 1985, "Sharq"),
    ("Shaytanat", "Tohir Malik", "badiiy", 1992, "Sharq"),
    ("Dunyoning ishlari", "O'tkir Hoshimov", "badiiy", 2007, "Sharq"),
    ("Yulduzli tunlar", "Pirimqul Qodirov", "badiiy", 1963, "Sharq"),
    ("Qo'shchinor", "Said Ahmad", "badiiy", 1978, "Sharq"),
    ("Uzoq yo'l", "Cholpon", "badiiy", 1925, "Turon"),
    ("Bolalik", "G'afur G'ulom", "badiiy", 1930, "Sharq"),
    ("Oq va qora", "Pirimqul Qodirov", "badiiy", 1958, "Sharq"),
    ("Yurak", "Said Ahmad", "badiiy", 1980, "Sharq"),
    ("Matematika 5-sinf", "O. Rustamov", "darslik", 2020, "O'qituvchi"),
    ("Matematika 6-sinf", "O. Rustamov", "darslik", 2021, "O'qituvchi"),
    ("Matematika 7-sinf", "O. Rustamov", "darslik", 2022, "O'qituvchi"),
    ("Fizika 8-sinf", "N. Tursunov", "darslik", 2020, "O'qituvchi"),
    ("Fizika 9-sinf", "N. Tursunov", "darslik", 2021, "O'qituvchi"),
    ("Kimyo 10-sinf", "Sh. Nazarov", "darslik", 2020, "O'qituvchi"),
    ("Kimyo 11-sinf", "Sh. Nazarov", "darslik", 2021, "O'qituvchi"),
    ("Tarix 5-sinf", "A. Karimov", "darslik", 2020, "O'qituvchi"),
    ("Tarix 6-sinf", "A. Karimov", "darslik", 2021, "O'qituvchi"),
    ("Tabiat fanlari 5-sinf", "M. Yusupov", "darslik", 2020, "O'qituvchi"),
    ("Tabiat fanlari 6-sinf", "M. Yusupov", "darslik", 2021, "O'qituvchi"),
    ("O'zbek tili 5-sinf", "Z. Mahmudov", "darslik", 2020, "O'qituvchi"),
    ("O'zbek tili 6-sinf", "Z. Mahmudov", "darslik", 2021, "O'qituvchi"),
    ("Ingliz tili 5-sinf", "J. Smith", "darslik", 2020, "O'qituvchi"),
    ("Ingliz tili 6-sinf", "J. Smith", "darslik", 2021, "O'qituvchi"),
    ("Adabiyot 7-sinf", "R. Rahimov", "darslik", 2022, "O'qituvchi"),
    ("Adabiyot 8-sinf", "R. Rahimov", "darslik", 2023, "O'qituvchi"),
    ("Adabiyot 9-sinf", "R. Rahimov", "darslik", 2022, "O'qituvchi"),
    ("Huquqshunoslik asoslari", "K. Normatov", "ilmiy", 2019, "Adolat"),
    ("Iqtisodiyot nazariyasi", "S. Sulaymonov", "ilmiy", 2020, "Iqtisod-moliya"),
    ("Psixologiya", "M. Mirzayev", "ilmiy", 2021, "Sharq"),
    ("Falsafa", "A. Alimov", "ilmiy", 2018, "Sharq"),
    ("Sotsiologiya", "N. Nabiyev", "ilmiy", 2022, "Sharq"),
    ("Kompyuter fanlari", "D. Davlatov", "ilmiy", 2023, "Aloqa"),
    ("Sun'iy intellekt", "R. Rustamov", "ilmiy", 2024, "Aloqa"),
    ("Ma'lumotlar bazasi", "S. Saydov", "ilmiy", 2022, "Aloqa"),
    ("Dasturlash asoslari", "A. Aliev", "ilmiy", 2021, "Aloqa"),
    ("Veb-dasturlash", "M. Murodov", "ilmiy", 2023, "Aloqa"),
    ("Mobil ilovalar", "K. Karimov", "ilmiy", 2024, "Aloqa"),
]

STUDENT_NAMES = [
    "Azizbek Karimov", "Malika Tursunova", "Jasur Rahimov", "Shahnoza Abdullayeva",
    "Bekzod Alimov", "Dilnoza Nazarova", "Farrux Yusupov", "Gulnoza Qodirova",
    "Ibrohim Mirzaev", "Kamola Saidova", "Lazizbek Normatov", "Madina Sulaymonova",
    "Nodirbek Nabiyev", "Ozoda Davlatova", "Qobiljon Saydov", "Ruhshona Alieva",
    "Sardor Murodov", "Tolib Karimov", "Umida Tursunova", "Viktor Rahimov",
    "Xurshid Abdullayev", "Yulduz Nazarova", "Zafar Yusupov", "Aida Qodirova",
    "Bahodir Mirzaev", "Charos Saidova", "Dilshod Normatov", "Elyor Sulaymonov",
    "Feruza Nabiyeva", "G'ayrat Davlatov",
]

TEACHER_NAMES = [
    "Prof. Akmal Karimov", "Doc. Malika Tursunova", "Prof. Jasur Rahimov",
    "Doc. Shahnoza Abdullayeva", "Prof. Bekzod Alimov", "Doc. Dilnoza Nazarova",
]

GENRES = ["badiiy", "darslik", "ilmiy", "bolalar", "tarixiy", "detektiv", "fantastika"]
PUBLISHERS = ["Sharq", "G'afur G'ulom", "O'qituvchi", "Adolat", "Iqtisod-moliya", "Aloqa", "Turon", "Yosh gvardiya"]
SHELVES = [f"{chr(65+i)}-{str(j).zfill(2)}" for i in range(5) for j in range(1, 21)]


def generate_isbn(index):
    """Generate a fake ISBN."""
    return f"978-9943-{str(index).zfill(2)}-{str(random.randint(10000, 99999))}-{random.randint(0, 9)}"


def generate_phone(index):
    """Generate a fake phone number."""
    return f"+9989{random.randint(0, 9)}{random.randint(1000000, 9999999)}"


def generate_card_number(year, index):
    """Generate a fake library card number."""
    return f"LIB-{year}-{str(index + 1000).zfill(4)}"


@transaction.atomic
def create_mock_data():
    print("Creating mock data...")
    
    # Create librarians
    librarians = []
    for i, name in enumerate(TEACHER_NAMES):
        user, created = User.objects.get_or_create(
            username=f"librarian_{i+1}",
            defaults={
                "full_name": name,
                "rol": "kutubxonachi",
                "is_staff": True,
            }
        )
        if created:
            user.set_password("lib12345")
            user.save()
        librarians.append(user)
    print(f"Created {len(librarians)} librarians")
    
    # Create books
    books = []
    for i, (nomi, muallif, janr, nashr_yili, nashriyot) in enumerate(BOOKS):
        book, created = Kitob.objects.get_or_create(
            isbn=generate_isbn(i),
            defaults={
                "nomi": nomi,
                "muallif": muallif,
                "janr": janr,
                "nashr_yili": nashr_yili,
                "nashriyot": nashriyot,
                "holati": "mavjud",
            }
        )
        books.append(book)
    print(f"Created {len(books)} books")
    
    # Create copies (nusxa) - 2-3 copies per book
    copies = []
    existing_count = Nusxa.objects.count()
    for book in books:
        num_copies = random.randint(2, 3)
        for j in range(num_copies):
            inv_num = existing_count + len(copies) + 1
            copy, created = Nusxa.objects.get_or_create(
                kitob=book,
                inventar_raqami=f"INV-{str(inv_num).zfill(6)}",
                defaults={
                    "holati": random.choice(["mavjud", "mavjud", "mavjud", "berilgan", "band"]),
                    "javon": random.choice(SHELVES),
                    "qabul_sana": now().date() - timedelta(days=random.randint(1, 365)),
                }
            )
            copies.append(copy)
    print(f"Created {len(copies)} copies")
    
    # Create students (oquvchi)
    students = []
    for i, name in enumerate(STUDENT_NAMES):
        student, created = Oquvchi.objects.get_or_create(
            telefon=generate_phone(i),
            defaults={
                "fish": name,
                "karta_raqami": generate_card_number(now().year, i+1),
                "sinf": f"{random.randint(5, 11)}-{random.choice(['A', 'B', 'C'])}",
            }
        )
        students.append(student)
    print(f"Created {len(students)} students")
    
    # Create teachers (o'qituvchi)
    teachers = []
    for i, name in enumerate(TEACHER_NAMES):
        teacher, created = Oquvchi.objects.get_or_create(
            telefon=generate_phone(100 + i),
            defaults={
                "fish": name,
                "karta_raqami": f"TEACH-{now().year}-{str(i+100).zfill(3)}",
                "kasb": random.choice(["Matematika", "Fizika", "Kimyo", "Biologiya", "Tarix", "O'zbek tili", "Ingliz tili", "Informatika"]),
            }
        )
        teachers.append(teacher)
    print(f"Created {len(teachers)} teachers")
    
    all_readers = students + teachers
    
    # Create active loans (berish)
    active_loans = 0
    overdue_loans = 0
    available_copies = [c for c in copies if c.holati == "mavjud"]
    
    # Active loans (not overdue)
    for _ in range(min(30, len(available_copies))):
        if not available_copies:
            break
        copy = random.choice(available_copies)
        available_copies.remove(copy)
        
        reader = random.choice(all_readers)
        librarian = random.choice(librarians)
        
        Berish.objects.get_or_create(
            nusxa=copy,
            kitob=copy.kitob,
            oquvchi=reader,
            defaults={
                "bergan_xodim": librarian,
                "berilgan_sana": now().date() - timedelta(days=random.randint(1, 10)),
                "qaytarish_muddati": now().date() + timedelta(days=random.randint(5, 20)),
                "holati": "faol",
            }
        )
        active_loans += 1
    
    # Overdue loans (for fines)
    for _ in range(min(15, len(available_copies))):
        if not available_copies:
            break
        copy = random.choice(available_copies)
        available_copies.remove(copy)
        
        reader = random.choice(all_readers)
        librarian = random.choice(librarians)
        
        Berish.objects.get_or_create(
            nusxa=copy,
            kitob=copy.kitob,
            oquvchi=reader,
            defaults={
                "bergan_xodim": librarian,
                "berilgan_sana": now().date() - timedelta(days=random.randint(20, 40)),
                "qaytarish_muddati": now().date() - timedelta(days=random.randint(1, 15)),
                "holati": "faol",
            }
        )
        overdue_loans += 1
    
    # Returned loans
    returned_loans = 0
    for _ in range(20):
        copy = random.choice(copies)
        reader = random.choice(all_readers)
        librarian = random.choice(librarians)
        
        Berish.objects.get_or_create(
            nusxa=copy,
            kitob=copy.kitob,
            oquvchi=reader,
            defaults={
                "bergan_xodim": librarian,
                "olgan_xodim": random.choice(librarians),
                "berilgan_sana": now().date() - timedelta(days=random.randint(30, 90)),
                "qaytarish_muddati": now().date() - timedelta(days=random.randint(10, 30)),
                "qaytarilgan_sana": now().date() - timedelta(days=random.randint(1, 10)),
                "holati": "qaytarilgan",
            }
        )
        returned_loans += 1
    
    print(f"Created {active_loans} active loans, {overdue_loans} overdue loans, {returned_loans} returned loans")
    
    # Create reservations (navbat)
    reservations = 0
    for book in random.sample(books, min(20, len(books))):
        # Check if all copies are borrowed or reserved
        book_copies = [c for c in copies if c.kitob == book]
        available = [c for c in book_copies if c.holati == "mavjud"]
        
        if len(available) < 2:  # Limited availability -> reservations
            for _ in range(random.randint(1, 4)):
                reader = random.choice(all_readers)
                # Check if already in queue
                if not Navbat.objects.filter(kitob=book, oquvchi=reader, holati="kutmoqda").exists():
                    Navbat.objects.get_or_create(
                        kitob=book,
                        oquvchi=reader,
                        defaults={"holati": "kutmoqda"}
                    )
                    reservations += 1
    
    print(f"Created {reservations} reservations")
    
    # Create some applications (ariza)
    applications = 0
    for i in range(10):
        phone = generate_phone(200 + i)
        if not Oquvchi.objects.filter(telefon=phone).exists():
            Ariza.objects.get_or_create(
                telegram_id=2000000 + i,
                defaults={
                    "rol": random.choice(["oquvchi", "oqituvchi"]),
                    "fish": f"Yangi Foydalanuvchi {i+1}",
                    "telefon": phone,
                    "sinf": f"{random.randint(5, 11)}-A" if random.choice([True, False]) else None,
                    "kasb": random.choice(["Matematika", "Fizika", "Kimyo"]) if random.choice([True, False]) else "",
                    "holati": random.choice(["kutmoqda", "tasdiqlandi", "bekor"]),
                }
            )
            applications += 1
    
    print(f"Created {applications} applications")
    
    # Run jarima calculation
    from jarima.tasks import jarimalarni_hisobla
    jarimalarni_hisobla()
    print("Calculated fines")
    
    print("\n✅ Mock data generation complete!")
    print(f"""
Summary:
- Librarians: {len(librarians)}
- Books: {len(books)}
- Copies: {len(copies)}
- Students: {len(students)}
- Teachers: {len(teachers)}
- Active loans: {active_loans}
- Overdue loans: {overdue_loans}
- Returned loans: {returned_loans}
- Reservations: {reservations}
- Applications: {applications}
""")


if __name__ == "__main__":
    create_mock_data()