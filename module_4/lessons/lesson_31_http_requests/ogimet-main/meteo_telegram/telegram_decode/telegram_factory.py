from .meteo_ogimet import TelegramProcessor

class TelegramFactory:
    @staticmethod
    def create_processor(country_code=None, start_date=None, end_date=None, **kwargs):

        match country_code:
            case 'bel':
                stations_list = TelegramProcessor.stations_list_by
                return TelegramProcessor(stations_list, start_date, end_date)

            case 'rus':
                stations_list = TelegramProcessor.stations_list_rus
                return TelegramProcessor(stations_list, start_date, end_date)

            case 'ua':
                stations_list = TelegramProcessor.stations_list_ua
                return TelegramProcessor(stations_list, start_date, end_date)

            case _:
                raise ValueError("Valid country_code must be provided")
