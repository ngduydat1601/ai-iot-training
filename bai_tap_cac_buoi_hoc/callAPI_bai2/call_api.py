import requests
import webbrowser
from dotenv import load_dotenv
import os
load_dotenv()
ACCESS_KEY = os.getenv("ACCESS_KEY")
query = input("Nhập từ khóa: ")

url = "https://api.unsplash.com/search/photos"

headers = {
    "Authorization": f"Client-ID {ACCESS_KEY}"
}

params = {
    "query": query,
    "per_page": 2,
    "orientation": "portrait"
    
}

response = requests.get(url, headers=headers, params=params)

data = response.json()

if len(data["results"]) > 0:
    image_url = data["results"][0]["urls"]["regular"]

    print("URL:", image_url)

    webbrowser.open(image_url)
else:
    print("Không tìm thấy ảnh.")
