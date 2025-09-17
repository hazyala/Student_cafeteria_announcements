import requests #웹사이트 방문
import json #데이터 정리
import time #정보 받아옴 기다림
import datetime #오늘 날짜와 요일 받아옴
import os #컴퓨터 시스템 정보
from selenium import webdriver #동적 웹사이트 크롤링 셀레니움
from selenium.webdriver.chrome.service import Service #셀레니움 도구   
from webdriver_manager.chrome import ChromeDriverManager #셀레니움 도구
from bs4 import BeautifulSoup #뷰티풀솝 HTML 해석도구

# --- 설정 ---
# 깃허브 Secret에 등록 예정
REST_API_KEY = os.environ.get('KAKAO_REST_API_KEY', '여기에 api키를 입력해주세요.') #카카오 restApi 키
TOKEN_FILE = "kakao_token.json" #토근 저장 파일

# --- 카카오 API 함수 ---

def refresh_access_token(): #임시 토근을 영구 토근으로 발급
    """Refresh Token을 사용하여 새로운 Access Token을 발급받습니다."""
    # try-except 구문: 오류처리 구문
    try:
        with open(TOKEN_FILE, "r") as fp: #json열기
            token_data = json.load(fp) #json 읽어서 token_data 변수에 저장
    except FileNotFoundError:
        print(f"Error: '{TOKEN_FILE}' 찾지 못했습니다. get_token.py 를 먼저 시행하세요.") #오류시 출력
        return None

    url = "https://kauth.kakao.com/oauth/token" #카카오 토큰 주소
    payload = { #카카오에 보낼 요청정보
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": token_data["refresh_token"],
    }
    response = requests.post(url, data=payload)  # requests.post 함수: 카카오 요청 회신
    new_token_data = response.json() #카카오에서 회신 받은 정보를 json으로 변환

    if 'access_token' in new_token_data: #카카오에서 회신받은 조건 확인
        print("토큰 발급 성공") 
        token_data.update(new_token_data) # token_data.update 함수: 기존 정보에 새로 받은 정보를 갱신
        with open(TOKEN_FILE, "w") as fp: #기존 정보에 파일을 덮어씌워 저장
            json.dump(token_data, fp)
        return token_data['access_token'] #저장한 토큰 반환하며 종료
    else:
        print(f"토큰 발급 실패: {new_token_data}")
        return None
    
#----메세지 발송------
def get_friends_list(token):
    """동의한 친구 목록을 가져옵니다."""
    url = "https://kapi.kakao.com/v1/api/talk/friends"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    friends_data = response.json()

    if "elements" in friends_data:
        friend_uuids = [friend["uuid"] for friend in friends_data["elements"]]
        print(f"Found {len(friend_uuids)} consented friends.")
        return friend_uuids
    else:
        print("No consented friends found or failed to get list:", friends_data)
        return []

def send_message_to_friend(token, uuid, text):
    """지정된 친구에게 메시지를 보냅니다."""
    url = "https://kapi.kakao.com/v1/api/talk/friends/message/default/send"
    headers = {"Authorization": f"Bearer {token}"}
    template = {"object_type": "text", "text": text, "link": {"web_url": "https://www.kopo.ac.kr/jungsu/content.do?menu=247"}}
    payload = {"receiver_uuids": json.dumps([uuid]), "template_object": json.dumps(template)}
    response = requests.post(url, headers=headers, data=payload)
    return response.json()

def send_message_to_me(token, text):
    """나에게 메시지를 보냅니다."""
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {token}"}
    template = {"object_type": "text", "text": text, "link": {"web_url": "https://www.kopo.ac.kr/jungsu/content.do?menu=247"}}
    payload = {"template_object": json.dumps(template)}
    response = requests.post(url, headers=headers, data=payload)
    return response.json()

# --- 학식 정보 수집 함수 ---
def format_menu(raw_text): #글자 서식 정렬
    """메뉴 텍스트의 서식을 정리합니다."""
    if not raw_text.strip():
        return "메뉴 정보 없음"
    
    # HTML 엔티티 '&amp;'를 '&' 문자로 변경하고 쉼표로 분리
    sanitized_text = raw_text.replace('&amp;', '&').replace(' ,', ',').replace(', ', ',')
    items = sanitized_text.split(',') # items 변수: 쉼표를 기준으로 메뉴들을 나누어 리스트로 저장
    
    formatted_items = [f"-{item.strip()}" for item in items if item.strip()] # formatted_items 변수: 각 메뉴 앞에 '-'를 붙여 새로운 배열(리스트)로 저장
    return "\n".join(formatted_items)

def get_menu(test_day=None): #웹사이트에서 학식 정보 받아옴
    """웹사이트에서 학식 메뉴를 가져옵니다."""
    day_names = ["월요일", "화요일", "수요일", "목요일", "금요일"]
    
    if test_day is not None:
        if 0 <= test_day < len(day_names):
            day_name = day_names[test_day]
            header = f"====📜 오늘의 학식 ({day_name}) TEST===="
            target_weekday = test_day
        else:
            return "잘못된 테스트 요일입니다."
    else:
        target_weekday = datetime.datetime.today().weekday()
        if target_weekday > 4:
            return "주말에는 운영하지 않습니다."
        day_name = day_names[target_weekday]
        header = f"====📜 오늘의 학식 ({day_name})===="
        
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    URL = "https://www.kopo.ac.kr/jungsu/content.do?menu=247"
    
    try:
        driver.get(URL)
        time.sleep(3)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
    finally:
        driver.quit()

    menu_table = soup.find("table", class_="tbl_table menu")
    if not menu_table:
        return "식단표를 찾을 수 없습니다."

    rows = menu_table.find("tbody").find_all("tr")
    if len(rows) <= target_weekday:
        return "해당 요일의 식단 정보가 없습니다."

    cells = rows[target_weekday].find_all("td")
    if len(cells) < 4:
        return "식단표의 형식이 변경되었습니다."
        
    lunch_menu = format_menu(cells[2].get_text(strip=True))
    dinner_menu = format_menu(cells[3].get_text(strip=True))
    
    return f"{header}\n\n  ============ 중식 ============\n{lunch_menu}\n\n  ============ 석식 ============\n{dinner_menu}"

# --- 메인 실행 ---
if __name__ == "__main__":
    # 테스트를 위해 요일을 지정합니다 (0=월, 1=화, 2=수, 3=목, 4=금)
    menu_text = get_menu() 
    print(menu_text)

    if any(keyword in menu_text for keyword in ["주말", "없습니다", "찾을 수 없음", "변경되었습니다"]):
        print(f"알림을 보낼 메뉴가 없습니다: {menu_text}")
    else:
        access_token = refresh_access_token()
        if access_token:
            print("\n--- 나에게 보내기 ---")
            my_response = send_message_to_me(access_token, menu_text)
            if my_response.get("result_code") == 0:
                print("메세지 발송 성공")
            else:
                print(f"메세지 발송 실패: {my_response}")

            friends = get_friends_list(access_token)
            if friends:
                print(f"\n--- 친구에게 {len(friends)} 보내기---")
                success_count = 0
                for friend_uuid in friends:
                    friend_response = send_message_to_friend(access_token, friend_uuid, menu_text)
                    if "successful_receiver_uuids" in friend_response:
                        success_count += 1
                
                print(f"{success_count}/{len(friends)} 친구에게보내기.")

            if not friends:
                print("모든 알림 발송 성공")
            elif success_count == len(friends):
                print("모든 알림 발송 성공")