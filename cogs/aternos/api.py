import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait


class AternosAPI:
    def __init__(self, username, password, server_address):
        self.username = username
        self.password = password
        self.server_address = server_address

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        self.driver = uc.Chrome(options=options)

    def start_server(self):
        self.driver.get("https://aternos.org/server")

        user_input = self.driver.find_element_by_id(id_="user")
        password_input = self.driver.find_element_by_id(id_="password")

        user_input.send_keys(self.username)
        password_input.send_keys(self.password)
        password_input.send_keys(Keys.RETURN)

        try:
            server_button = WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((By.CLASS_NAME, "server-body"))
            )
            server_button.click()

            start_button = WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((By.ID, "start"))
            )
            start_button.click()

            status_label = WebDriverWait(self.driver, 10).until(
                ec.text_to_be_present_in_element(
                    (By.CLASS_NAME, "statuslabel-label"), "Preparing"
                )
            )
        except Exception as e:
            self.driver.quit()
            raise e
