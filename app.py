import streamlit as st
import requests
import json
import hmac
import hashlib
from time import gmtime, strftime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import re

def modify_url(input_url):
    # Selenium WebDriver 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    
    # 입력된 URL에 접속
    driver.get(input_url)
    final_url_with_js = driver.current_url
    driver.quit()
    
    # URL에서 '&lptag' 부분을 수정
    modified_url = re.sub(r'&lptag=[^&]*(&|$)', '&', final_url_with_js)
    modified_url = modified_url.rstrip('&')  # 불필요한 '&' 제거
    
    return modified_url

def generate_hmac(method, url, secret_key, access_key):
    path, *query = url.split("?")
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetime_gmt + method + path + (query[0] if query else "")
    
    signature = hmac.new(bytes(secret_key, "utf-8"),
                         message.encode("utf-8"),
                         hashlib.sha256).hexdigest()
    
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_gmt}, signature={signature}"

st.title('URL Modifier')

input_url = st.text_input("Enter your URL here:")

if st.button("Modify URL"):
    modified_url = modify_url(input_url)  # URL 수정 함수 호출
    
    # 쿠팡 API로 요청 보내기
    REQUEST_METHOD = "POST"
    DOMAIN = "https://api-gateway.coupang.com"
    URL = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    ACCESS_KEY = "YOUR_ACCESS_KEY"
    SECRET_KEY = "YOUR_SECRET_KEY"
    REQUEST = {"coupangUrls": [modified_url]}
    
    authorization = generate_hmac(REQUEST_METHOD, URL, SECRET_KEY, ACCESS_KEY)
    url = "{}{}".format(DOMAIN, URL)
    response = requests.request(method=REQUEST_METHOD, url=url,
                                headers={
                                    "Authorization": authorization,
                                    "Content-Type": "application/json"
                                },
                                data=json.dumps(REQUEST))
    
    response_data = response.json()
    
    if 'data' in response_data and len(response_data['data']) > 0:
        shorten_url = response_data['data'][0].get('shortenUrl', 'URL not found')
        st.write('Shorten URL:', shorten_url)
    else:
        st.write('No data found or invalid response')
