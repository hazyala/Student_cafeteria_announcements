import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def format_menu(raw_text):
    if "없습니다" in raw_text or not raw_text.strip():
        return "메뉴 정보가 없습니다."
    items = raw_text.split(',')
    formatted_items = [f"-{item.strip()}" for item in items if item.strip()]
    return "\n".join(formatted_items)

def get_menu(test_day=None):
    if test_day is not None:
        target_weekday = test_day
        day_name = ["월요일", "화요일", "수요일", "목요일", "금요일"][target_weekday]
        header = f"== {day_name} 메뉴 TEST =="
    else:
        target_weekday = datetime.datetime.today().weekday()
        if target_weekday > 4:
            return "오늘은 주말이므로 학식이 운영되지 않습니다."
        header = "== 오늘의 메뉴 =="

    # 웹사이트 수집 정보
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
        return "게시판을 찾았지만 내용이 비어있습니다."

    rows = menu_table.find("tbody").find_all("tr")
    
    if len(rows) <= target_weekday:
        return f"게시판에 해당 요일의 정보가 없습니다."

    cells = rows[target_weekday].find_all("td")
    
    if len(cells) < 4:
        return "게시판의 형식이 예상과 달라 메뉴를 읽을 수 없습니다."
        
    lunch_menu_raw = cells[2].get_text(strip=True)
    dinner_menu_raw = cells[3].get_text(strip=True)

    lunch_menu = format_menu(lunch_menu_raw)
    dinner_menu = format_menu(dinner_menu_raw)

    result = (
        f"{header}\n\n"
        f"== 중식 ==\n"
        f"{lunch_menu}\n\n"
        f"== 석식 ==\n"
        f"{dinner_menu}"
    )
    
    return result

# --- 시작 ---
if __name__ == "__main__":
    # 임시지정 test_day= 요일값 (0=월, 1=화, 2=수, 3=목, 4=금) 자동화시 get_menu()만 사용
    print(get_menu())