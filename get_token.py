import requests
import json
REST_API_KEY = '2fd626e04ea552b8debb9562ee3e78b7'
AUTHORIZATION_CODE = 'WIT5aFzmY0j1SeoR7sF4HW10mh4noSG3M8AVAKiXq4WRF34G2r2HVAAAAAQKFyIgAAABmVZQgEBSGUcvaFb1Eg'
REDIRECT_URI = 'https://localhost:3000'
url = "https://kauth.kakao.com/oauth/token"
payload = {"grant_type": "authorization_code", "client_id": REST_API_KEY, "redirect_uri": REDIRECT_URI, "code": AUTHORIZATION_CODE}
response = requests.post(url, data=payload)
token_data = response.json()
if 'refresh_token' in token_data:
    print("Refresh Token 발급 성공")
    with open("kakao_token.json", "w") as fp:
        json.dump(token_data, fp)
    print("=> 'kakao_token.json' 파일에 저장 성공")
else:
    print("토큰 발급 실패:", token_data)