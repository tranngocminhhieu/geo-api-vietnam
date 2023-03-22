import os
import random
import re
import sqlite3
import warnings

import numpy as np
import pandas as pd
import requests
from geopy.geocoders import Nominatim
from tenacity import *
from unidecode import unidecode
import appdirs
from fuzzywuzzy import fuzz

warnings.filterwarnings('ignore')

# Variables
geoapivietnam_sqlite_file = appdirs.user_data_dir('geoapivietnam/geoapivietnam.db')
data_dir = os.path.join(os.path.dirname(__file__), 'data')
df_valid_provinces = pd.read_excel(os.path.join(data_dir, 'valid_provinces.xlsx'))
df_vn = pd.read_excel(os.path.join(data_dir, 'gso_province_district_ward.xlsx'))
df_vn_district = df_vn[['province', 'district', 'province_sul', 'district_sul']].drop_duplicates().reset_index(drop=True)

def color(color_name):
    # ANSI escape sequences
    color_codes = {
        'Black': 30,
        'Red': 31,
        'Green': 32,
        'Yellow': 33,
        'Blue': 34,
        'Magenta': 35,
        'Cyan': 36,
        'White': 37,
        'Default': 0
    }
    return f"\033[{color_codes.get(color_name.capitalize())}m"

# Get Short Unidecode Lower (SUL) data
def get_province_sul(province):
    province_ul = unidecode(str(province).lower())
    for i in [r'^tinh\s', r'^thanh\spho\s', r'^tp.']:
        if re.search(i, province_ul):
            province_ul = re.sub(i, '', province_ul).strip()
            break
    return province_ul

def get_district_sul(district):
    district_ul = unidecode(str(district).lower())
    if re.search(r'quan [0-9]{1,2}', district_ul):
        pass
    else:
        for i in [r'^quan\s', '^q\.', r'^huyen\s', r'^h\.', r'^thi xa\s', r'^tx\.', r'^xa\s', r'^x\.',
                  r'^thanh pho\s',
                  r'^tp\.']:
            if re.search(i, district_ul):
                district_ul = re.sub(i, '', district_ul).strip()
                break
    return district_ul

def get_ward_sul(ward):
    ward_ul = unidecode(str(ward).lower())
    if re.search(r'phuong [0-9]{1,2}', ward_ul):
        pass
    else:
        for i in [r'^phuong\s', r'^thi\stran\s', r'^xa\s', r'^huyen\s']:
            if re.search(i, ward_ul):
                ward_ul = re.sub(i, '', ward_ul).strip()
                break
    return ward_ul

# Sqlite actions
class SqliteActions:
    def __init__(self, database=geoapivietnam_sqlite_file):
        self.database = database
        self.create_database()

    def create_database(self):
        # Create the folder if it doesn't exist
        self.create_folder_if_not_exists(self.database)

        # Establish a connection to the database
        with sqlite3.connect(self.database) as conn:
            # Create the historical_search table if it doesn't already exist
            conn.execute('''
                CREATE TABLE IF NOT EXISTS historical_search (
                    search_term TEXT PRIMARY KEY,
                    address VARCHAR,
                    province VARCHAR,
                    district VARCHAR,
                    ward VARCHAR,
                    latitude FLOAT,
                    longitude FLOAT,
                    source VARCHAR,
                    original_address VARCHAR
                )
            ''')

    def select_location_from_database(self, search_term):
        # Query the database for the address corresponding to the given geo
        with sqlite3.connect(self.database) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM historical_search WHERE search_term = ?', (search_term,))
            result = cursor.fetchone()
            if result:
                # If a result was found, return it as a dict
                return dict(result)
            else:
                # If no data was found, return 'No-data'
                return 'No-data'

    def append_or_update_data(self, search_term, json_data):
        # Check if the search_term already exists in the table
        with sqlite3.connect(self.database) as conn:
            cursor = conn.execute('SELECT search_term FROM historical_search WHERE search_term = ?', (search_term,))
            result = cursor.fetchone()
            if result:
                # If the search_term exists, update the corresponding row
                conn.execute('''UPDATE historical_search SET
                                address = ?,
                                province = ?,
                                district = ?,
                                ward = ?,
                                latitude = ?,
                                longitude = ?,
                                source = ?,
                                original_address = ?
                                WHERE search_term = ?''',
                             (json_data['address'], json_data['province'], json_data['district'],
                              json_data['ward'], json_data['latitude'], json_data['longitude'],
                              json_data['source'], json_data['original_address'], search_term))
            else:
                # If the search_term doesn't exist, insert a new row with the given data
                conn.execute('''INSERT INTO historical_search (
                                    search_term, address, province, district, ward,
                                    latitude, longitude, source, original_address)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (search_term, json_data['address'], json_data['province'], json_data['district'],
                              json_data['ward'], json_data['latitude'], json_data['longitude'],
                              json_data['source'], json_data['original_address']))
            # Commit the changes to the database
            conn.commit()

    def delete_data(self, search_term):
        # Check if the search_term value exists in the table
        with sqlite3.connect(self.database) as conn:
            cursor = conn.execute('SELECT search_term FROM historical_search WHERE search_term = ?', (search_term,))
            result = cursor.fetchone()
            if result:
                # If the search_term value exists, delete the corresponding row
                conn.execute('DELETE FROM historical_search WHERE search_term = ?', (search_term,))
                # Commit the changes to the database
                conn.commit()
            else:
                # If the search_term value doesn't exist, print an error message
                print(f"Error: search_term value '{search_term}' does not exist in the table.")

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
    def __init__(self, use_fuzzy=True, print_result=True):
        self.use_fuzzy = use_fuzzy
        self.print_result = print_result
    def get_fuzzy_ratio(self, string_1, string_2):
        string_1_ul = unidecode(str(string_1).lower())
        string_2_ul = unidecode(str(string_2).lower())
        return fuzz.ratio(string_1_ul, string_2_ul)

    def correct_province(self, province, fuzzy_ratio=95):
        '''

        :param province: Input province name information as string.
        :return: Output province name correctly.
        '''
        province_sul = get_province_sul(province)
        for o, a_sul, in zip(df_valid_provinces.original_province, df_valid_provinces.alias_province_sul):

            if a_sul in province_sul:
                if self.print_result:
                    print(f'{color("White")}{province}{color("Default")} is correct to {color("Green")}{o}{color("Default")}')
                return o

            if self.use_fuzzy:
                ratio = self.get_fuzzy_ratio(a_sul, province_sul)
                if ratio >= fuzzy_ratio:
                    if self.print_result:
                        print(f'{color("White")}{province}{color("Default")} is correct to {color("Green")}{o}{color("Default")} by Fuzzy!')
                    return o

        return 'No-data'

    def correct_district(self, province, district, fuzzy_ratio_province=95, fuzzy_ratio_district=95):
        '''

        :param province: Input province name correctly as string.
        :param district: Input district name information as string.
        :return: Output district name correctly.
        '''
        province_sul = get_province_sul(province)
        district_sul = get_district_sul(district)

        # Search
        for p_sul, d_sul, d in zip(df_vn_district.province_sul, df_vn_district.district_sul, df_vn_district.district):

            if province_sul in p_sul and district_sul in d_sul:
                return d

            if self.use_fuzzy:
                ratio_1 = self.get_fuzzy_ratio(province_sul, p_sul)
                ratio_2 = self.get_fuzzy_ratio(district_sul, d_sul)
                if ratio_1 >= fuzzy_ratio_province and ratio_2 >= fuzzy_ratio_district:
                    return d

        return 'No-data'

# Object
class Location:
    def __init__(self, address=None, province=None, district=None, ward=None, latitude=None, longitude=None, source=None, original_address=None):
        self.address = address
        self.province = province
        self.district = district
        self.ward = ward
        self.latitude = latitude
        self.longitude = longitude
        self.source = source
        self.original_address = original_address
        self.json_data = {
            'address': self.address,
            'province': self.province,
            'district': self.district,
            'ward': self.ward,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'source': self.source,
            'original_address': self.original_address
        }

    def __repr__(self):
        object_show = f'address: {self.address}, province: {self.province}, district: {self.district}, ward: {self.ward}, latitude: {self.latitude}, longitude: {self.longitude}, source: {self.source}, original_address: {self.original_address}'
        return object_show
# Main
class GetLocation:
    def __init__(self, database=geoapivietnam_sqlite_file, google_maps_api_key=None, force_data_excel=None, print_result=True):
        self.database = database
        self.sqlite_actions = SqliteActions(database=self.database)
        self.correct = Correct(print_result=False)
        self.print_result = print_result
        self.google_maps_api_key = google_maps_api_key
        self.force_data_excel = force_data_excel

    def build_location(self, address, latitude, longitude, source):
        address_ul = unidecode(str(address).lower())

        # Prevent Google result District X or Ward X (X is number)
        address_ul = address_ul.replace('district', 'quan').replace('ward', 'phuong')

        address_split = address_ul.split(',')
        address_split = [i.strip() for i in address_split if (i.strip().isnumeric()==False and i.strip() not in ['vietnam', 'viet nam'])]
        address_split.reverse()

        # Find province
        province = None # Set default if not match

        for part in address_split:
            for o, a_sul in zip(df_valid_provinces.original_province, df_valid_provinces.alias_province_sul):
                if a_sul in part:
                    province = o
                    break
            if province != None:
                break

        # Find district
        districts = df_vn[df_vn.short_province == province][['district', 'district_sul']].drop_duplicates()
        district = None
        for d, d_sul in zip(districts.district, districts.district_sul):

            # Prevent quan 1 match with quan 1X
            if re.search(r'quan [0-9]{1,2}', d_sul):
                our_district_number = int(d_sul.split(" ")[-1])
                find_address_district = re.findall(r'quan [0-9]{1,2}', address_ul)
                if len(find_address_district):
                    address_district_number = int(find_address_district[0].split(" ")[-1])
                    if address_district_number == our_district_number:
                        district = d
                        break

            elif d_sul in address_ul:
                district = d
                break
            else:
                district = None

        # if district == None: # GeoPy can return an address missing province (10.2262425, 103.9725849), need to improve
        #     pass

        # Find ward
        wards = df_vn[(df_vn.short_province == province) & (df_vn.district == district)][['ward', 'ward_sul']]
        ward = None
        for w, w_sul in zip(wards.ward, wards.ward_sul):
            # Search
            # Pevent phuong 1 match with phuong 1X
            if re.search(r'phuong [0-9]{1,2}', w_sul):
                our_ward_number = int(w_sul.split(" ")[-1])
                find_address_ward = re.findall(r'phuong [0-9]{1,2}', address_ul)
                if len(find_address_ward):
                    address_ward_number = int(find_address_ward[0].split(" ")[-1])
                    if address_ward_number == our_ward_number:
                        ward = w
                        break

            elif w_sul in address_ul:
                ward = w
                break

            else:
                ward = None

        new_address = f'{ward + ", " if ward != None else ""}{district + ", " if district != None else ""}{province if province != None else ""}'

        return Location(address=new_address, province=province, district=district, ward=ward, latitude=latitude, longitude=longitude,
                        source=source, original_address=address)

    @retry(wait=wait_fixed(30), stop=stop_after_attempt(10))
    def geopy_get_location(self, search_term, user_agent='myGeocoder', random_user_agent_number=True):
        if random_user_agent_number:
            user_agent = f'{user_agent}{random.choice(list(range(1000)))}'
        locator = Nominatim(user_agent=user_agent)
        try:
            location = locator.geocode(search_term)
            address = location.address
            latitude = location.latitude
            longitude = location.longitude
            source = 'GeoPy'

            return self.build_location(address=address, latitude=latitude, longitude=longitude, source=source)

        except Exception as e:
            print(color('Red'), f'GeoPy: {e}')
            return Location(source='GeoPy', original_address=f'Error: {e}')

    @retry(wait=wait_fixed(30), stop=stop_after_attempt(10))
    def google_get_location(self, search_term, maps_api_key=None):
        if maps_api_key == None:
            maps_api_key = self.google_maps_api_key

        url = f'https://maps.googleapis.com/maps/api/geocode/json?address={search_term}&key={maps_api_key}'
        try:
            res = requests.get(url)
            data = res.json()

            if data.get('error_message') != None:
                print(color('Red'), f'Google: {data.get("error_message")}')
                return Location(source='Google', original_address=f'Error: {data.get("error_message")}')

            latitude = data['results'][0]['geometry']['location']['lat']
            longitude = data['results'][0]['geometry']['location']['lng']
            address = data['results'][0]['formatted_address']
            source = 'Google'

            return self.build_location(address=address, latitude=latitude, longitude=longitude, source=source)

        except Exception as e:
            return Location(source='Google', original_address=f'Error: {e}')

    def excel_get_location(self, search_term, force_data_excel=None):
        if force_data_excel == None:
            force_data_excel = self.force_data_excel

        if force_data_excel != None and os.path.isfile(force_data_excel) == False:
            self.sqlite_actions.create_folder_if_not_exists(my_path=force_data_excel)
            pd.DataFrame(columns=['search_term', 'address', 'latitude', 'longitude']).to_excel(force_data_excel,
                                                                                               index=False)

        force_data = pd.read_excel(force_data_excel)
        search_data = force_data[force_data.search_term == search_term].reset_index(drop=True)
        search_data = search_data.replace({np.nan: None})

        source = 'Excel'

        if search_data.shape[0]:
            address = search_data.address.to_list()[0]
            latitude = search_data.latitude.to_list()[0]
            longitude = search_data.longitude.to_list()[0]

            return self.build_location(address=address, latitude=latitude, longitude=longitude, source=source)
        else:
            return Location(source=source, original_address='No-data')
        
    def sqlite_get_location(self, search_term):
        source = 'SQLite'
        search_result = self.sqlite_actions.select_location_from_database(search_term=search_term)
        if search_result != 'No-data':

            return Location(address=search_result['address'],
                            province=search_result['province'],
                            district=search_result['district'],
                            ward=search_result['ward'],
                            latitude=search_result['latitude'],
                            longitude=search_result['longitude'],
                            source=search_result['source'] + ' (SQLite)',
                            original_address=search_result['original_address'])
        else:
            return Location(source=source, original_address='No-data')
            
    def manual_get_location(self, address, latitude=None, longitude=None, source='Manual'):
        return self.build_location(address=address, latitude=latitude, longitude=longitude, source=source)

    def get_location(self, search_term, force_data_excel=None, google_maps_api_key=None):
        if force_data_excel == None:
            force_data_excel = self.force_data_excel
        if google_maps_api_key == None:
            google_maps_api_key = self.google_maps_api_key

        # From Excel first
        if force_data_excel != None and os.path.isfile(force_data_excel):
            location = self.excel_get_location(search_term=search_term, force_data_excel=force_data_excel)
            if location.original_address != 'No-data':
                return location

        # From SQLite second
        location = self.sqlite_get_location(search_term=search_term)
        if location.original_address != 'No-data' and location.province != None:
            return location

        # From GeoPy third
        try:
            location = self.geopy_get_location(search_term=search_term)
            if 'Error' not in location.original_address and location.province != None:
                self.sqlite_actions.append_or_update_data(search_term=search_term, json_data=location.json_data)
                return location
        except Exception as e:
            location = Location(source='GeoPy', original_address=f'Error: {e}')

        # From Google API forth
        if google_maps_api_key != None:
            try:
                location = self.google_get_location(search_term=search_term)
                if 'Error' not in location.original_address:
                    self.sqlite_actions.append_or_update_data(search_term=search_term, json_data=location.json_data)
                    return location
            except Exception as e:
                location = Location(source='Google', original_address=f'Error: {e}')

        return location

    def check_if_district_in_address(self, district, address):
        district_sul = get_district_sul(district)
        address_ul = unidecode(str(address).lower())

        if district_sul in address_ul:
            return True
        else:
            return False

    def get_district_from_address_miss_province(self, province, address):
        province_sul = get_province_sul(province)
        address_ul = unidecode(str(address).lower())

        address_ul = address_ul.replace('hanoi', 'ha noi')

        search_province = df_vn_district.province_sul.str.contains(province_sul)

        # Remove long-Province to reduce mistake (Thanh pho Lai Chau, Tinh Lai Chau)
        try:
            long_province = unidecode(str(df_vn_district[search_province].province.tolist()[0]).lower())
            address_ul = address_ul.replace(long_province, '')
        except:
            pass

        search_district = df_vn_district.district.apply(self.check_if_district_in_address, address=address_ul)

        try:
            district = df_vn_district[search_province & search_district].district.tolist()[0]
        except:
            district = 'No-data'

        return district

    def get_valid_district(self, province, search_term, force_data_excel=None, google_maps_api_key=None, print_result=None):

        if province == None or province == '' or province == 'No-data':
            print(f'{color("Red")}Province is invalid ({province}), skip and return "Province-invalid"!')
            return 'Province-invalid'

        if force_data_excel == None:
            force_data_excel = self.force_data_excel
        if google_maps_api_key == None:
            google_maps_api_key = self.google_maps_api_key
        if print_result == None:
            print_result = self.print_result

        search_term = str(search_term)
        province = self.correct.correct_province(province)

        # Get address
        location = self.get_location(search_term=search_term, google_maps_api_key=google_maps_api_key, force_data_excel=force_data_excel)

        if location.province == province and location.district != None:
            if print_result:
                print(f'{color("Green")}{location.district}{color("Default")} match with {color("Green")}{province}{color("Default")} perfect! {color("White")}({location.source})')
            return location.district

        if location.province == None and 'No-data' not in location.original_address and 'Error' not in location.original_address:
            district = self.get_district_from_address_miss_province(province=province, address=location.original_address)
            if district != 'No-data':
                if print_result:
                    print(f'{color("Green")}{district}{color("Default")} match with {color("Green")}{province}{color("Default")} when missing info! {color("White")}({location.source})')
                return district

        if (location.source not in ['Google', 'Excel']) and (google_maps_api_key != None):
            try:
                location = self.google_get_location(search_term=search_term, maps_api_key=google_maps_api_key)
                self.sqlite_actions.append_or_update_data(search_term=search_term, json_data=location.json_data)
                if location.province == province and location.district != None:
                    if print_result:
                        print(f'{color("Green")}{location.district}{color("Default")} match with {color("Green")}{province}{color("Default")} perfect! {color("White")}({location.source})')
                    return location.district
            except Exception as e:
                location = Location(source='Google', original_address=f'Error: {e}')

        # Can not find district from address, return address to explore later
        print(f'Can not match {color("Red")}{location.address}{color("Default")} with {color("Red")}{province}{color("Default")}, return address! {color("White")}({location.source})')
        return f'Not-match: {location.address} ({location.source})'
