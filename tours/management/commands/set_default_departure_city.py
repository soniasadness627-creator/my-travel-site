from django.core.management.base import BaseCommand
from tours.models import Tour

class Command(BaseCommand):
    help = 'Встановлює значення за замовчуванням для departure_city в усіх турах'

    def handle(self, *args, **options):
        updated = Tour.objects.filter(departure_city__isnull=True).update(departure_city='Київ')
        self.stdout.write(self.style.SUCCESS(f'Оновлено {updated} турів'))