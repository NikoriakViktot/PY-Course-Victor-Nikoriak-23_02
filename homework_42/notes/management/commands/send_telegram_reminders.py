from django.core.management.base import BaseCommand

from notes.telegram import publish_due_reminders


class Command(BaseCommand):
    help = "Send due note reminders to the configured Telegram channel."

    def handle(self, *args, **options):
        sent_count, failed_count = publish_due_reminders()
        self.stdout.write(
            self.style.SUCCESS(
                f"Telegram reminders sent: {sent_count}; skipped/failed: {failed_count}."
            )
        )