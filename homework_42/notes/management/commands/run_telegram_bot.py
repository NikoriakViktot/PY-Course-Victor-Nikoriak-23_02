from django.core.management.base import BaseCommand

from notes.telegram import TelegramBotClient, handle_telegram_update


class Command(BaseCommand):
    help = "Run the Telegram notes bot with long polling."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Process currently available updates once and exit.",
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=None,
            help="Telegram update offset to start from.",
        )

    def handle(self, *args, **options):
        client = TelegramBotClient()
        if not client.has_token:
            self.stdout.write(
                self.style.WARNING("TELEGRAM_BOT_TOKEN is not configured.")
            )
            return

        offset = options["offset"]
        self.stdout.write(self.style.SUCCESS("Telegram notes bot started."))
        while True:
            updates = client.get_updates(offset=offset)
            for update in updates:
                offset = update["update_id"] + 1
                handle_telegram_update(update, client=client)

            if options["once"]:
                self.stdout.write(
                    self.style.SUCCESS("Telegram notes bot processed one batch.")
                )
                return