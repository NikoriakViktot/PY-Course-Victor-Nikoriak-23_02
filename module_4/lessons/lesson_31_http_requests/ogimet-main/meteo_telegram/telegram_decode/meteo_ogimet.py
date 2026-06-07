import re
import requests
from datetime import datetime, timedelta
import pandas as pd
import io
from fake_useragent import UserAgent

from .class_metedecode import TelegramMeteoDecoder

def get_user_agent():
    return UserAgent().random

class TelegramProcessor:
    stations_list_by = [
        '26554',
        '26643',
        '26645',
        '26653',
        '26657',
        '26659',
        '26666',
        '26668',
        '26759',
        '26763',
        '26774',
        '26832',
        '26850',
        '26853',
        '26855',
        '26864',
        '26878',
        '26887',
        '26941',
        '26951',
        '26961',
        '26966',
        '33008',
        '33019',
        '33027',
        '33036',
        '33038',
        '33041',
        '33124',
    ]
    stations_list_rus = [
        '26585',
        '26578',
        '26578',
        '26695',
        '26976',
        '26781',
        '26898',
        '34009',
        '34003',
        '34202',
        '27707',
        '26997',
        '27906',
        '26882',
        '26898',
        '26894',
        '26898',
        '34009',
        '26898',
        '34110',
        '26976',
        '34009',
        '26784',
        '34109',
        '26882',
        '26795',
        '34214',
        '34110',
        '34321',
        '34202',
        '34213',
        '34116',
        '34336',
        '34535',
        '34438',
    ]
    stations_list_ua = [
        '33088',
        '33135',
        '33177',
        '33261',
        '33275',
        '33301',
        '33317',
        '33325',
        '33345',
        '33377',
        '33393',
        '33415',
        '33429',
        '33466',
        '33506',
        '33526',
        '33562',
        '33587',
        '33614',
        '33631',
        '33658',
        '33663',
        '33711',
        '33761',
        '33791',
        '33837',
        '33902',
        '33924',
        '33946',
        '33983',
        '33998',
        '34300',
        '34415',
        '34504',
        '34601',
        '34712'
    ]

    request_link = 'http://www.ogimet.com/cgi-bin/getsynop'
    def __init__(self, stations_list, start_date=None, end_date=None):
            self.stations_list = stations_list
            self.start_date = start_date if start_date is not None else datetime.now() - timedelta(days=3)
            self.end_date = end_date if end_date is not None else datetime.now()
            self.decoder = TelegramMeteoDecoder()

    def get_station_data(self, wmo: str, start_date: datetime, end_date: datetime):
        start_date_str = start_date.strftime("%Y%m%d%H%M")
        end_date_str = end_date.strftime("%Y%m%d%H%M")
        params = {'block': wmo, 'begin': start_date_str, 'end': end_date_str}
        headers = {
            'User-Agent': get_user_agent()
        }
        response = requests.get(self.request_link, params=params, headers=headers)

        if response.status_code == 200:
            try:
                csv_file_like_object = io.StringIO(response.text)
                headers = ['station_id', 'year', 'month', 'day', 'hour', 'minute', 'telegram']
                df = pd.read_csv(csv_file_like_object, names=headers)
                df = df.drop('minute', axis=1)
                return df
            except Exception as e:
                print("Error processing response as CSV:", e)
                return None
        else:
            print(f"Request failed: {response.status_code}\n{response.text}")
            return None

    def get_telegrams(self, stations_list, start_date: datetime, end_date: datetime):
        all_telegrams_dfs = []
        for station in stations_list:
            df = self.get_station_data(station, start_date, end_date)
            if df is not None:
                all_telegrams_dfs.append(df)

        if all_telegrams_dfs:
            all_telegrams_df = pd.concat(all_telegrams_dfs)
            return all_telegrams_df
        else:
            return pd.DataFrame()

    def decode_telegrams(self, df):
        decoded_data = []
        for _, row in df.iterrows():
            telegram = re.sub(r'=+$', '', row['telegram'])
            base_data = {
                    'id_telegram': f"{row['station_id']}{row['year']}{row['month']}{row['day']}{row['hour']}",
                    'station_id': row['station_id'],
                    'year': row['year'],
                    'month': row['month'],
                    'day': row['day'],
                    'hour': row['hour'],
                    'telegram': telegram
                }
            self.decoder.decode(telegram)
            if self.decoder.decoded_response:
                decoded_values = self.decoder.get_decoded_data()
                base_data.update(decoded_values)
                decoded_data.append(base_data)
        return pd.DataFrame(decoded_data)

    def process_telegrams(self):
        df = self.get_telegrams(self.stations_list, self.start_date, self.end_date)
        decoded_df = self.decode_telegrams(df)
        return decoded_df
