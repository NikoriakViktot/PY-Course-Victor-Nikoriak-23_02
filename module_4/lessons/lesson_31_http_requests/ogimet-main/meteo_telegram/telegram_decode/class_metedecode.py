import math
from pymetdecoder import synop
from . import meteo_logger


class CustomSYNOP(synop.SYNOP):
    def __init__(self):
        super().__init__()

    def decode(self, message):
        try:
            decoded_data = super().decode(message)
            return decoded_data
        except Exception as ex:
            meteo_logger.error(f"Error decoding telegram: {message} - {ex}", exc_info=True)
            raise

class TelegramMeteoDecoder:
    def __init__(self):
        self.decoded_response = None
        self.decoder = CustomSYNOP()

    def decode(self, telegram):
        try:
            decoded_data = self.decoder.decode(telegram)
            self.decoded_response = decoded_data
            return self.decoded_response
        except Exception as ex:
            meteo_logger.error(f"Error decoding telegram: {telegram} - {ex}", exc_info=True)


    def get_nested_value(self, *args):
        """
        Отримує значення з вкладеного словника використовуючи послідовність ключів.
        """
        value = self.decoded_response
        for arg in args:
            if isinstance(value, dict) and arg in value:
                value = value[arg]
            else:
                return None
        return value

    def get_station_id(self):
        return self.get_nested_value('station_id', 'value')

    def get_temperature(self):
        return self.get_nested_value('air_temperature', 'value')

    def get_dew_point_temperature(self):
        return self.get_nested_value( 'dewpoint_temperature', 'value')

    def calculate_relative_humidity(self, T, T_d):
        if T is not None and T_d is not None:
            relative_humidity = 100 * math.exp((17.62 * T_d) / (243.12 + T_d) - (17.62 * T) / (243.12 + T))
            return round(relative_humidity)
        return None

    def get_date_telegram(self):
        return self.get_nested_value( 'obs_time')

    def get_wind(self):

        wind_dir = self.get_nested_value('surface_wind', 'direction', 'value')
        wind_speed = self.get_nested_value('surface_wind', 'speed', 'value')
        return wind_dir, wind_speed

    def decode_and_get_section5(self, telegram):
        decoded_data = self.decoder._decode(telegram)
        section5_data = decoded_data.get("section5", [])
        return section5_data

    def get_pressure(self):
        return self.get_nested_value('station_pressure', 'value')

    def get_sea_level_pressure(self):
        return self.get_nested_value('sea_level_pressure', 'value')

    def get_maximum_temperature(self):
        return self.get_nested_value('maximum_temperature', 'value')

    def get_minimum_temperature(self):
        return self.get_nested_value('minimum_temperature', 'value')

    def get_precipitation_s1(self):
        return {'amount': self.get_nested_value('precipitation_s1', 'amount', 'value'),
                'time_before_obs': self.get_nested_value('precipitation_s1', 'time_before_obs', 'value')}

    def get_precipitation_s3(self):
        return {
            'amount': self.get_nested_value('precipitation_s3', 'amount', 'value'),
            'time_before_obs': self.get_nested_value('precipitation_s3', 'time_before_obs', 'value')
        }

    def get_pressure_tendency(self):
        return {
            'tendency': self.get_nested_value('pressure_tendency', 'tendency', 'value'),
            'change': self.get_nested_value('pressure_tendency', 'change', 'value')
        }

    def get_present_weather(self):
        return self.get_nested_value('present_weather', 'value')

    def get_past_weather(self):
        past_weather = self.get_nested_value('past_weather')
        if past_weather and isinstance(past_weather, list) and len(past_weather) >= 2:
            if isinstance(past_weather[0], dict) and isinstance(past_weather[1], dict):
                value1 = past_weather[0].get('value')
                value2 = past_weather[1].get('value')
                return value1, value2
            else:
                return None, None
        else:
            return None, None

    def get_sunshine(self):
        return self.get_nested_value('sunshine', 0, 'amount', 'value')

    def get_ground_state_snow(self):
        return {
            'state': self.get_nested_value('ground_state_snow', 'state', 'value'),
            'depth': self.get_nested_value('ground_state_snow', 'depth', 'depth')
        }

    def get_ground_state(self):
        return {
            'state': self.get_nested_value('ground_state', 'state', 'value'),
            'temperature_soil_surface': self.get_nested_value('ground_state', 'temperature', 'value')
        }
    def get_decoded_data(self):
        wind_dir, wind_speed = self.get_wind()
        past_weather_1, past_weather_2 = self.get_past_weather()
        return {
                'station_id': self.get_station_id(),
                'date_telegram': self.get_date_telegram(),
                 'temperature': self.get_temperature(),
                'dew_point_temperature': self.get_dew_point_temperature(),
                'relative_humidity': self.calculate_relative_humidity(self.get_temperature(),
                                                                      self.get_dew_point_temperature()),
                'wind_dir': wind_dir,
                'wind_speed': wind_speed,
                'pressure': self.get_pressure(),
                'sea_level_pressure': self.get_sea_level_pressure(),
                'maximum_temperature': self.get_maximum_temperature(),
                'minimum_temperature': self.get_minimum_temperature(),
                'precipitation_s1': self.get_precipitation_s1(),
                'precipitation_s3': self.get_precipitation_s3(),
                'pressure_tendency': self.get_pressure_tendency(),
                'present_weather': self.get_present_weather(),
                'past_weather_1': past_weather_1,
                'past_weather_2': past_weather_2,
                'sunshine': self.get_sunshine(),
                'ground_state_snow': self.get_ground_state_snow(),
                'ground_state': self.get_ground_state()

            }