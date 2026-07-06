import requests

url = "https://harryknowsball.com/api"

headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(url, headers=headers)

print(r.status_code)
print(r.text[:1000])