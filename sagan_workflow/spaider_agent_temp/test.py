import httpx

response = httpx.get('https://api.openai.com')
print(response.status_code)