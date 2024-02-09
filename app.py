import streamlit as st
import requests
import json
import hmac
import hashlib
from time import gmtime, strftime

# 단축된 URL을 확장하는 함수
def expand_url(input_url):
    # unshorten.me API를 사용하여 단축 URL 확장
    response = requests.get(f"https://unshorten.me/s/{input_url}")
    if response.status_code == 200:
        # 정상적으로 URL이 확장되었다면, 결과를 반환
        return response.text
    else:
        # 오류가 발생했다면, 오류 메시지 반환
        return "URL could not be resolved."

# 쿠팡 파트너스 API를 사용하여 확장된 URL 처리
def modify_url_with_coupang_api(expanded_url):
    REQUEST_METHOD = "POST"
    DOMAIN = "https://api-gateway.coupang.com"
    URL = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    ACCESS_KEY = "672762f9-2fcf-492f-b0f0-fa9a9667c48d"  # 여기에 실제 ACCESS_KEY 입력
    SECRET_KEY = "be00679970176587de0377745befa932aa233ea3"  # 여기에 실제 SECRET_KEY 입력
    REQUEST = {"coupangUrls": [expanded_url]}
    
    authorization = generate_hmac(REQUEST_METHOD, URL, SECRET_KEY, ACCESS_KEY)
    url = f"{DOMAIN}{URL}"
    response = requests.request(method=REQUEST_METHOD, url=url, headers={
        "Authorization": authorization,
        "Content-Type": "application/json"
    }, data=json.dumps(REQUEST))
    
    return response.json()

def generate_hmac(method, url, secret_key, access_key):
    path, *query = url.split("?")
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetime_gmt + method + path + (query[0] if query else "")
    
    signature = hmac.new(bytes(secret_key, "utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_gmt}, signature={signature}"

st.title('URL Modifier')

input_url = st.text_input("Enter your URL here:")

if st.button("Modify URL"):
    expanded_url = expand_url(input_url)
    
    if expanded_url != "URL could not be resolved.":
        response_data = modify_url_with_coupang_api(expanded_url)
        if 'data' in response_data and len(response_data['data']) > 0:
            shorten_url = response_data['data'][0].get('shortenUrl', 'URL not found')
            text_to_copy = f"쿠팡이 추천합니다!\n{shorten_url}"
            
            copy_button = f"<button onclick=\"navigator.clipboard.writeText('{text_to_copy}')\">Copy to Clipboard</button>"
            st.markdown(copy_button, unsafe_allow_html=True)
            st.write('Coupang Shorten URL:', shorten_url)
            
        else:
            st.write('No data found or invalid response with Coupang API.')
    else:
        st.write(expanded_url)
