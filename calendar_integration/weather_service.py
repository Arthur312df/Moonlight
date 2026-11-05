import requests

def get_current_location():
    try:
        # Detecta a cidade e país com base no IP público atual
        response = requests.get("https://ipapi.co/json/", timeout=3)
        if response.status_code == 200:
            data = response.json()
            city = data.get("city", "Brasília")
            country = data.get("country_name", "Brazil")
            return f"{city}, {country}"
    except Exception:
        pass
    return "Brasília, Brazil"  # Fallback padrão

def get_weather_for_user():
    location = get_current_location()
    try:
        # O wttr.in aceita o nome da cidade dinamicamente
        url = f"https://wttr.in/{location.replace(' ', '+')}?format=j1"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            temp_c = current['temp_C']
            desc = current['weatherDesc'][0]['value']
            return location, f"{temp_c}°C com {desc.lower()}"
    except Exception:
        pass
    return location, "clima indisponível"