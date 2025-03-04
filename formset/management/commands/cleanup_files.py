from datetime import timedelta

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from formset.upload import UPLOAD_TEMP_DIR


class Command(BaseCommand):
    help = "Delete all dangling files from their temporary storage"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            action='store',
            nargs='?',
            default=30,
            type=int,
        )

    def handle(self, *args, **options):
        days = options['days']
        num_files = 0
        _, temp_files = default_storage.listdir(UPLOAD_TEMP_DIR)
        for temp_file in temp_files:
            created_time = default_storage.get_created_time(UPLOAD_TEMP_DIR / temp_file)
            if created_time < now() - timedelta(days=days):
                default_storage.delete(UPLOAD_TEMP_DIR / temp_file)
                num_files += 1
        self.stdout.write(f"Removed {num_files} files older than {days} days from temporary storage.")
