from selenium import webdriver
from selenium.webdriver.common.by import By
from pymongo import MongoClient
import re

# اتصال به دیتابیس MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['test_db2']  # نام دیتابیس
collection = db['test_results']  # نام کلکسیون

# راه اندازی Selenium WebDriver
driver = webdriver.Chrome()

# باز کردن صفحه وب
driver.get("https://e-rasaneh.ir/Register_Person.aspx")

# پیدا کردن تمامی فیلدهای ورودی
input_fields = driver.find_elements(By.XPATH, "//input[@type='text']")

# داده های تست مختلف
test_data = ["test123", "123456", "!@#test", "9876543210", "abc1234567", "john@example.com", "noemail@wrong"]

# استثنا برای فیلدهای خاص
field_exceptions = {
    "ContentPlaceHolder1_tbxNationalCode": lambda data: data.isdigit() and len(data) == 10,
    "ContentPlaceHolder1_tbxName": lambda data: data.isalpha(),
    "ContentPlaceHolder1_tbxFamily": lambda data: data.isalpha(),
    "ContentPlaceHolder1_tbxEmail": lambda data: re.match(r"^[^\s]+@.*\.com$", data) is not None,
    "ContentPlaceHolder1_UC_CAPTCHA_tbxCaptcha": lambda data: data.isdigit()
}

# پیام خطا برای فیلدهای خاص
error_messages = {
    "ContentPlaceHolder1_tbxNationalCode": "National code must be a 10-digit number",
    "ContentPlaceHolder1_tbxName": "Name must contain only letters",
    "ContentPlaceHolder1_tbxFamily": "Family name must contain only letters",
    "ContentPlaceHolder1_tbxEmail": "Email must not contain spaces and must end with @***.com",
    "ContentPlaceHolder1_UC_CAPTCHA_tbxCaptcha": "Captcha must contain only numbers"
}

# حلقه برای تست هر فیلد ورودی
for index, field in enumerate(input_fields):
    field_xpath = driver.execute_script("return arguments[0].xpath;", field)  # گرفتن XPath یا متد دقیق‌تر
    field_id = field.get_attribute('id') or f'field_{index}'  # استفاده از id یا index
    test_results = []

    # بررسی هر ورودی با داده‌های تست
    for data in test_data:
        try:
            field.clear()
            field.send_keys(data)
            print(f"Testing with data: {data} at XPath: {field_xpath}")

            # بررسی استثنا برای فیلدهای خاص
            if field_id in field_exceptions:
                if not field_exceptions[field_id](data):
                    error_message = error_messages[field_id]
                    print(f"Error: {error_message} for input: {data}")
                    # ذخیره خطا در MongoDB
                    test_results.append({
                        "test_data": data,
                        "result": f"failed: {error_message}"
                    })
                    continue  # ادامه ندادن به تست برای این ورودی نادرست
                else:
                    test_results.append({
                        "test_data": data,
                        "result": "success"
                    })
            else:
                # برای سایر فیلدها، نتیجه موفقیت‌آمیز ثبت می‌شود
                test_results.append({
                    "test_data": data,
                    "result": "success"
                })

        except Exception as e:
            print(f"Error interacting with field at XPath: {field_xpath}")
            # ذخیره اطلاعات خطا در MongoDB
            test_results.append({
                "test_data": data,
                "result": f"failed: {str(e)}"
            })
    
    # ذخیره اطلاعات در MongoDB به صورت والد-فرزند
    collection.insert_one({
        "field_xpath": field_xpath,
        "field_id": field_id,
        "tests": test_results
    })

# بستن WebDriver
driver.quit()
