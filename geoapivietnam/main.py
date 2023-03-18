import os
import random
import re
import sqlite3
import warnings

import pandas as pd
import requests
from geopy.geocoders import Nominatim
from tenacity import *
from unidecode import unidecode

warnings.filterwarnings('ignore')


# Sqlite actions
class SqliteActions:
    def __init__(self, database='../data/data.db'):
        self.database = database
        self.create_database()

    def create_database(self):
        # Create the folder if it doesn't exist
        self.create_folder_if_not_exists(self.database)

        # Establish a connection to the database
        with sqlite3.connect(self.database) as conn:
            # Create the historical_geo table if it doesn't already exist
            conn.execute('''
                CREATE TABLE IF NOT EXISTS historical_geo (
                    geo TEXT PRIMARY KEY,
                    address VARCHAR
                )
            ''')

    def sqlite_select_address_from_database(self, geo):
        # Query the database for the address corresponding to the given geo
        with sqlite3.connect(self.database) as conn:
            cursor = conn.execute('SELECT address FROM historical_geo WHERE geo = ?', (geo,))
            result = cursor.fetchone()
            if result:
                # If a result was found, return it as a string
                return result[0]
            else:
                # If no data was found, return 'No-data'
                return 'No-data'

    def sqlite_append_or_update_data(self, geo, address):
        # Check if the geo value already exists in the table
        with sqlite3.connect(self.database) as conn:
            cursor = conn.execute('SELECT geo FROM historical_geo WHERE geo = ?', (geo,))
            result = cursor.fetchone()
            if result:
                # If the geo value exists, update the corresponding address
                conn.execute('UPDATE historical_geo SET address = ? WHERE geo = ?', (address, geo))
            else:
                # If the geo value doesn't exist, insert a new row with the given geo and address
                conn.execute('INSERT INTO historical_geo (geo, address) VALUES (?, ?)', (geo, address))
            # Commit the changes to the database
            conn.commit()

    def sqlite_delete_data(self, geo):
        # Check if the geo value exists in the table
        with sqlite3.connect(self.database) as conn:
            cursor = conn.execute('SELECT geo FROM historical_geo WHERE geo = ?', (geo,))
            result = cursor.fetchone()
            if result:
                # If the geo value exists, delete the corresponding row
                conn.execute('DELETE FROM historical_geo WHERE geo = ?', (geo,))
                # Commit the changes to the database
                conn.commit()
            else:
                # If the geo value doesn't exist, print an error message
                print(f"Error: geo value '{geo}' does not exist in the table.")

    def create_folder_if_not_exists(self, my_path):
        # Check if the input path contains a directory
        if os.path.dirname(my_path):
            # If the input path contains a directory, use it
            my_dir = os.path.dirname(my_path)
        else:
            # If the input path does not contain a directory, assume it is a file name
            my_dir = '.'

        # Create the directory if it doesn't exist
        if not os.path.exists(my_dir):
            os.makedirs(my_dir)


class Correct:
    def __init__(self):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.df_valid_provinces = pd.read_excel(os.path.join(data_dir, 'valid_provinces.xlsx'))
        self.df_vn = pd.read_excel(os.path.join(data_dir, 'gso_province_district_ward.xlsx'))
        self.df_vn_district = self.df_vn[['province', 'district']].drop_duplicates().reset_index(drop=True)

    def correct_province(self, province):
        province_ul = unidecode(str(province).lower())
        for o, a, in zip(self.df_valid_provinces.original_province, self.df_valid_provinces.alias_province):
            o_ul = unidecode(str(o).lower())
            a_ul = unidecode(str(a).lower())

            if a_ul in province_ul:
                return o
        return 'No-data'

    def correct_district(self, province, district):
        province_ul = unidecode(str(province).lower())
        district_ul = unidecode(str(district).lower())

        # Remove prefix
        if re.search(r'quan [0-9]{1,2}', district_ul):
            pass
        else:
            for i in [r'^quan\s', '^q\.', r'^huyen\s', r'^h\.', r'^thi xa\s', r'^tx\.', r'^xa\s', r'^x\.',
                      r'^thanh pho\s',
                      r'^tp\.']:
                if re.search(i, district_ul):
                    district_ul = re.sub(i, '', district_ul).strip()
                    break

        # Search
        for p, d in zip(self.df_vn_district.province, self.df_vn_district.district):
            p_ul = unidecode(str(p).lower())
            d_ul = unidecode(str(d).lower())

            if province_ul in p_ul and district_ul in d_ul:
                return d

        return 'No-data'


# Main
class GetLocation:
    def __init__(self, database='../data/data.db', google_maps_api_key=None, force_data_excel=None, print_result=True):
        self.database = database
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.df_vn = pd.read_excel(os.path.join(data_dir, 'gso_province_district_ward.xlsx'))
        self.df_vn_district = self.df_vn[['province', 'district']].drop_duplicates().reset_index(drop=True)
        self.sqlite_actions = SqliteActions(database=self.database)
        self.print_result = print_result
        self.google_maps_api_key = google_maps_api_key
        self.force_data_excel = force_data_excel

    @retry(wait=wait_fixed(30), stop=stop_after_attempt(10))
    def geopy_get_address(self, search_term, user_agent='myGeocoder', random_user_agent_number=True):
        if random_user_agent_number:
            user_agent = f'{user_agent}{random.choice(list(range(1000)))}'
        locator = Nominatim(user_agent=user_agent)
        location = locator.geocode(search_term)
        try:
            address = location.address
            return address
        except:
            return 'No-data'

    def google_get_address(self, search_term, maps_api_key=None):
        if maps_api_key == None:
            maps_api_key = self.google_maps_api_key

        url = f'https://maps.googleapis.com/maps/api/geocode/json?address={search_term}&key={maps_api_key}'
        try:
            res = requests.get(url)
            return res.json()['results'][0]['formatted_address']
        except Exception as e:
            return f'Google API error: {e}'

    def get_address(self, search_term, force_data_excel=None, google_maps_api_key=None, print_result=None):
        if force_data_excel == None:
            force_data_excel = self.force_data_excel

        if google_maps_api_key == None:
            google_maps_api_key == self.google_maps_api_key

        if print_result == None:
            print_result = self.print_result

        # Get from Excel
        if force_data_excel != None and os.path.isfile(force_data_excel):
            force_data = pd.read_excel(force_data_excel)
            try:
                list_address = force_data[force_data.geo == search_term].address.values.tolist()
                if len(list_address):
                    address = list_address[0]
                    if print_result:
                        print(f'Excel: {search_term} = {address}')
                    return address + ' (by Excel)'
            except:
                self.sqlite_actions.create_folder_if_not_exists(my_path=force_data_excel)
                pd.DataFrame({'geo': [], 'address': []}).to_excel(force_data_excel, index=False)

        # Get from SQLite
        self.sqlite_actions.create_database()
        address = self.sqlite_actions.sqlite_select_address_from_database(geo=search_term)
        if address != 'No-data':
            if print_result:
                print(f'SQLite: {search_term} = {address}')
            return address + ' (Saved data from SQlite)'

        # Get from GeoPy
        address = self.geopy_get_address(search_term=search_term)
        if address != 'No-data':
            self.sqlite_actions.sqlite_append_or_update_data(geo=search_term, address=address + ' (by GeoPy)')
            if print_result:
                print(f'GeoPy: {search_term} = {address}')
            return address + ' (by GeoPy)'
        else:

            # Get from Google API
            if google_maps_api_key != None:
                address = self.google_get_address(search_term=search_term, maps_api_key=google_maps_api_key)
                if 'error' not in address.lower():
                    self.sqlite_actions.sqlite_append_or_update_data(geo=search_term, address=address + ' (by Google)')
                    if print_result:
                        print(f'Google Geocoding: {search_term} = {address}')
                    return address + ' (by Google)'

        # Can not found at all
        if print_result:
            print(f'Can not found {search_term} at all')
        return 'No-data'

    def search_district_from_address(self, district, address):
        district_ul = unidecode(district.lower())
        address_ul = unidecode(address.lower())

        # Remove prefix
        if re.search(r'quan [0-9]{1,2}', district_ul):
            pass
        else:
            for i in [r'^quan\s', '^q\.', r'^huyen\s', r'^h\.', r'^thi xa\s', r'^tx\.', r'^xa\s', r'^x\.',
                      r'^thanh pho\s',
                      r'^tp\.']:
                if re.search(i, district_ul):
                    district_ul = re.sub(i, '', district_ul).strip()
                    break

        if district_ul in address_ul:
            return True
        else:
            return False

    def get_district_from_address_miss_province(self, province, address):
        province_ul = unidecode(str(province).lower())
        address_ul = unidecode(str(address).lower())

        search_province = self.df_vn_district.province.apply(unidecode).str.lower().str.contains(province_ul)

        # Remove long-Province to reduce mistake
        long_province = unidecode(str(self.df_vn_district[search_province].province.tolist()[0]).lower())
        address_ul = address_ul.replace(long_province, '')

        search_district = self.df_vn_district.district.apply(self.search_district_from_address, address=address_ul)

        try:
            district = self.df_vn_district[search_province & search_district].district.tolist()[0]
        except:
            district = 'No-data'

        return district

    def extract_district_match_province(self, province, address, print_result=None):
        if print_result == None:
            print_result = self.print_result

        province_ul = unidecode(str(province).lower())

        replaces = {'Hanoi': 'Hà Nội'}
        for i in replaces:
            address = address.replace(i, replaces[i])

        # Split address to list and reverse to repare for For loop (Province -> District -> Ward -> Street)
        address_mod = address.split(', ')
        address_mod = [i for i in address_mod if i.isnumeric() == False]  # Remove zip code
        address_mod.reverse()

        # Loop from left to right to search Province, we will have District on the right side
        for i in address_mod:
            if province_ul in unidecode(str(i).lower()):
                try:  # Avoid no index for district error
                    district = address_mod[address_mod.index(i) + 1]
                    district = Correct().correct_district(province=province, district=district)
                    if print_result:
                        print(f'-> {district} district match with {province} province perfect!')
                    return district
                except:
                    pass

        # Miss Province in address
        district = self.get_district_from_address_miss_province(province=province_ul, address=address)
        district = Correct().correct_district(province=province, district=district)
        if district != 'No-data':
            if print_result:
                print(f'-> {district} district match with {province} province when missing info!')
            return district

        print(f'-> Can not match district for {province} province by this address!')
        return 'No-data'

    def get_district(self, province, search_term, force_data_excel=None, google_maps_api_key=None,
                     print_result=None):

        if force_data_excel == None:
            force_data_excel = self.force_data_excel

        if google_maps_api_key == None:
            google_maps_api_key = self.google_maps_api_key

        if print_result == None:
            print_result = self.print_result

        search_term = str(search_term)

        # Get address
        address = self.get_address(search_term=search_term, force_data_excel=force_data_excel,
                                   google_maps_api_key=google_maps_api_key, print_result=print_result)
        if address == 'No-data':
            return 'No-data'

        district = self.extract_district_match_province(province, address, print_result=print_result)
        if district != 'No-data':
            return district

        if ('by Google' not in address) and ('by Excel' not in address) and (google_maps_api_key != None):
            address = self.google_get_address(search_term, google_maps_api_key) + ' (by Google)'
            self.sqlite_actions.sqlite_append_or_update_data(geo=search_term, address=address)
            print(f'-> Get new address from Google API: {address}')
            district = self.extract_district_match_province(province, address, print_result=print_result)
            if district != 'No-data':
                return district

        # Can not find district from address, return address to explore later
        print(f'-> Can not match district for {province} province, return address!')
        return address
