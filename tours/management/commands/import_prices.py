import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from tours.models import Tour, PriceCalendar


class Command(BaseCommand):
    help = 'Імпорт цін з CSV файлу'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Шлях до CSV файлу')

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tour = Tour.objects.filter(title=row['tour_title']).first()
                if not tour:
                    self.stdout.write(self.style.WARNING(f"Тур '{row['tour_title']}' не знайдено"))
                    continue

                PriceCalendar.objects.update_or_create(
                    tour=tour,
                    date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                    duration=row['duration'],
                    defaults={'price': row['price']}
                )
                self.stdout.write(f"✅ Додано: {tour.title} - {row['date']} - {row['price']} грн")