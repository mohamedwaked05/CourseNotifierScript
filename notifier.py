from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()
USERNAME = os.getenv("UNI_USERNAME")
PASSWORD = os.getenv("UNI_PASSWORD")
COURSE_CODE = os.getenv("COURSE_CODE")

# Configuration
LOGIN_URL = "https://syslb.liu.edu.lb/login/"
REGISTRATION_URL = "https://syslb.liu.edu.lb/student/myRegistration/registrationByCourse.php"
SEMESTER_NAME = "Fall 2025 - 2026"
WAIT_TIMEOUT = 20
HEADLESS = False  # Set to True after testing

def setup_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver

def login(driver):
    try:
        print("\n[1/4] Logging in...")
        driver.get(LOGIN_URL)
        
        username = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "USER")))
        password = driver.find_element(By.ID, "PASS")
        login_btn = driver.find_element(By.XPATH, "//input[@type='image' and contains(@src, 'login_11.jpg')]")
        
        username.clear()
        username.send_keys(USERNAME)
        password.clear()
        password.send_keys(PASSWORD)
        
        ActionChains(driver).move_to_element(login_btn).click().perform()
        time.sleep(3)
        
        if "login" in driver.current_url.lower():
            raise Exception("Login failed - check credentials")
        print("✓ Login successful")
        return True
        
    except Exception as e:
        print(f"✗ Login failed: {str(e)}")
        driver.save_screenshot("login_failed.png")
        return False

def handle_semester_selection(driver):
    try:
        print("\n[2/4] Handling semester selection...")

        driver.get("https://syslb.liu.edu.lb/student/myRegistration/choicesPage.php")
        time.sleep(2)

        print("Current URL before semester selection:", driver.current_url)
        driver.save_screenshot("before_semester_selection.png")
        with open("before_semester_selection.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        # Check if the dropdown is inside an iframe; if yes, switch to it
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            print(f"Found {len(iframes)} iframe(s), switching to the first one")
            driver.switch_to.frame(iframes[0])
        else:
            print("No iframe found on semester selection page")

        dropdown_wrapper = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".jqTransformSelectWrapper"))
        )
        trigger_div = dropdown_wrapper.find_element(By.TAG_NAME, "div")
        ActionChains(driver).move_to_element(trigger_div).click().perform()
        print("✓ Opened semester dropdown")

        options_container = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".jqTransformSelectWrapper ul"))
        )
        options = options_container.find_elements(By.TAG_NAME, "li")

        for option in options:
            if SEMESTER_NAME in option.text:
                ActionChains(driver).move_to_element(option).click().perform()
                print(f"✓ Selected semester: {SEMESTER_NAME}")
                time.sleep(2)
                # Switch back to default content after iframe interaction
                if iframes:
                    driver.switch_to.default_content()
                return True

        print(f"✗ Semester '{SEMESTER_NAME}' not found in dropdown")
        driver.save_screenshot("semester_not_found.png")
        # Switch back even if not found
        if iframes:
            driver.switch_to.default_content()
        return False

    except Exception as e:
        print(f"✗ Semester selection failed: {str(e)}")
        driver.save_screenshot("semester_selection_failed.png")
        return False


    except Exception as e:
        print(f"✗ Semester selection failed: {str(e)}")
        driver.save_screenshot("semester_selection_failed.png")
        return False

def go_to_registration_page(driver):
    try:
        print("\n[3/4] Navigating directly to registration page...")

        # Wait to ensure the previous page fully loaded (semester dashboard)
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, "//b[contains(text(), 'Chosen Semester')]"))
        )
        print("✓ Semester dashboard loaded")

        # Directly load the registration page URL
        driver.get(REGISTRATION_URL)
        print(f"✓ Navigated directly to {REGISTRATION_URL}")
        time.sleep(2)  # wait for page to load

        return True

    except Exception as e:
        print(f"✗ Failed to navigate to registration page: {str(e)}")
        driver.save_screenshot("registration_navigation_failed.png")
        return False


def check_course_availability(driver):
    try:
        print("\n[4/4] Checking course availability...")

        try:
            block_msg = driver.find_element(By.XPATH, "//*[contains(text(), 'not allowed to register')]")
            print(f"⚠️ Registration blocked: {block_msg.text}")
            return False
        except NoSuchElementException:
            pass

        try:
            table = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'data')]"))
            )
            try:
                course_row = table.find_element(By.XPATH, f".//tr[td[contains(text(), '{COURSE_CODE}')]]")
                status = course_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]").text

                if "Open" in status or "Available" in status:
                    print(f"✅ Course {COURSE_CODE} is AVAILABLE!")
                    return True
                print(f"❌ Course {COURSE_CODE} status: {status}")
                return False

            except NoSuchElementException:
                print(f"Course {COURSE_CODE} not found in registration table")
                return False

        except TimeoutException:
            print("No registration table found")
            return False

    except Exception as e:
        print(f"✗ Course check failed: {str(e)}")
        driver.save_screenshot("course_check_failed.png")
        return False

def main():
    driver = setup_driver()
    try:
        if not login(driver):
            return
        if not handle_semester_selection(driver):
            return
        if not go_to_registration_page(driver):
            return
        check_course_availability(driver)
    except Exception as e:
        print(f"✗ Script failed: {str(e)}")
        driver.save_screenshot("main_error.png")
    finally:
        driver.quit()
        print("\nScript completed")

if __name__ == "__main__":
    main()
