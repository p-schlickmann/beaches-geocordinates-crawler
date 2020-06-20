import re
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as SeleniumEXC
from PIL import Image
import pytesseract

from conn import DatabaseConnection


class Scraper:
    def __init__(self, database_path, **kwargs):
        self.database_path = database_path
        self.driver = webdriver.Chrome('C:/Users/edu/Downloads/driver/chromedriver.exe')
        self.state = kwargs.get('state', None)
        self.city = kwargs.get('city', None)
        self.beach = kwargs.get('beach', None)

    def select_from_db(self):
        if self.beach:
            with DatabaseConnection(self.database_path) as cursor:
                select_query = "SELECT * FROM locations_2 WHERE beach=?"
                results = cursor.execute(select_query, (self.beach,))
                return results.fetchall()
        elif self.city:
            with DatabaseConnection(self.database_path) as cursor:
                select_query = "SELECT * FROM locations_2 WHERE city=?"
                results = cursor.execute(select_query, (self.city,))
                return results.fetchall()
        elif self.state:
            with DatabaseConnection(self.database_path) as cursor:
                select_query = "SELECT * FROM locations_2 WHERE state=?"
                results = cursor.execute(select_query, (self.state,))
                return results.fetchall()
        else:
            with DatabaseConnection(self.database_path) as cursor:
                select_query = "SELECT * FROM locations_2"
                results = cursor.execute(select_query)
                return results.fetchall()

    def main(self, db_rows, path_to_save_data, path_to_db):
        if db_rows:
            for idx, row in enumerate(db_rows):
                beach_name = row[2]
                city_name = row[1]
                state_name = row[0]
                wind_key = row[3]
                was_successful = self.search_coords(idx, state_name, city_name, beach_name, wind_key,
                                                    path_to_save_data, path_to_db)
                if not was_successful:
                    similar = self.similar_name(beach_name)
                    second_try = self.search_coords(idx, state_name, city_name, similar, wind_key,
                                                    path_to_save_data, path_to_db)
                    if not second_try:
                        print(f'problem with coords at {beach_name}')

    def search_coords(self, idx, state, city, beach, wind_key, path_to_save_data, path_to_db):
        bot = self.driver
        bot.get('https://www.google.com/')
        element = WebDriverWait(bot, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="tsf"]/div[2]/div[1]/div[1]/div/div[2]/input')))
        element.click()
        element.send_keys(f'{beach} {city} coordinates')
        element.send_keys(Keys.ENTER)
        try:
            WebDriverWait(bot, 1).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="Rzn5id"]/div/a[2]'))).click()
        except SeleniumEXC.TimeoutException:
            pass
        try:
            bot.find_element_by_xpath(
                '/html/body/div[6]/div[2]/div[9]/div[1]/div[2]/div/div[1]/div[2]/div/p/a[1]').click()
        except SeleniumEXC.NoSuchElementException:
            pass
        try:
            only_eng_pref = bot.find_element_by_xpath(
                '/html/body/div[6]/div[2]/div[9]/div[1]/div[2]/div/div[1]/div[2]/div/div/a[1]')
        except SeleniumEXC.NoSuchElementException:
            coords_crop = (200, 350, 900, 450)
            coords = self.save_coords(coords_crop, path_to_save_data, beach, city)
            lat, lon = self.check_coords(coords, beach)
            if lat and lon:
                self.save_to_db(state, city, beach, wind_key, lat, lon, path_to_db)
                return True
            else:
                return False
        else:
            lower_crop = (150, 400, 900, 500)
            coords = self.save_coords(lower_crop, path_to_save_data, beach, city)
            lat, lon = self.check_coords(coords, beach)
            if lat and lon:
                self.save_to_db(state, city, beach, wind_key, lat, lon, path_to_db)
                return True
            else:
                only_eng_pref.click()
                sleep(0.5)
                coords_crop = (200, 350, 900, 450)
                coords = self.save_coords(coords_crop, path_to_save_data, beach, city)
                lat, lon = self.check_coords(coords, beach)
                if lat and lon:
                    self.save_to_db(state, city, beach, wind_key, lat, lon, path_to_db)
                    return True
                else:
                    return False

    def save_coords(self, crop_coords, path_to_save_data, beach, city):
        bot = self.driver
        full_path = f'{path_to_save_data}/{city}#{beach}.png'
        bot.save_screenshot(full_path)
        coords_image = Image.open(full_path)
        cropped_coords = coords_image.crop(crop_coords)
        get_path = f'{path_to_save_data}/#{city}#{beach}.png'
        cropped_coords.save(get_path)
        return pytesseract.image_to_string(get_path)

    @staticmethod
    def check_coords(content, beach):
        expression = '(.+)(°|") (S|W), (.+)(°|") (S|W)'
        matches = re.search(expression, content)

        try:
            matches.group(0)
        except AttributeError:
            return False, False
        else:
            minus = ['W', 'S']
            lat = matches.group(1)
            signal_1 = matches.group(3)
            lon = matches.group(4)
            signal_2 = matches.group(6)
            if signal_1 in minus:
                try:
                    final_lat = float(lat) - 2 * float(lat)
                except ValueError:
                    lat_2 = lat.replace(' ', '')
                    try:
                        final_lat = float(lat_2) - 2 * float(lat_2)
                    except:
                        print(f'problem with {beach} coords')
            if signal_2 in minus:
                try:
                    final_lon = float(lon) - 2 * float(lon)
                except ValueError:
                    lon_2 = lon.replace(' ', '')
                    try:
                        final_lon = float(lon_2) - 2 * float(lon_2)
                    except:
                        print(f'problem with {beach} coords')
            try:
                return final_lat, final_lon
            except NameError:
                return None, None
            except:
                return None, None

    @staticmethod
    def save_to_db(state, city, beach, wind, lat, lon, path_to_db):
        with DatabaseConnection(path_to_db) as cursor:
            cursor.execute('INSERT INTO locations_4 VALUES (?,?,?,?,?,?)',
                           (state, city, beach, wind, lat, lon))

    @staticmethod
    def similar_name(name):
        expression = r'(Praia|Prainha|praia|prainha|Canto|canto)( Do| Da| De| Di| Du| Dos| Das| Des| Dis| Dus| | do| dos| das| da| des| de)(.+)'
        matches = re.search(expression, name)
        try:
            filtered_name = matches.group(3)
        except AttributeError:
            print(f'error with regex filtering in {name}')
        else:
            return filtered_name


scraper = Scraper('./scraper/database/brazil_1.db')
rows = scraper.select_from_db()
scraper.main(rows, './testando', './scraper/database/brazil_1.db')
