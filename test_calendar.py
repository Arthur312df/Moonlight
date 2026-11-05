import os
import datetime
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Escopos necessários para ler o calendário
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_current_location():
    try:
        response = requests.get("https://ipapi.co/json/", timeout=3)
        if response.status_code == 200:
            data = response.json()
            city = data.get("city", "Brasília")
            country = data.get("country_name", "Brazil")
            return f"{city}, {country}"
    except Exception:
        pass
    return "Brasília, Brazil"

def get_weather_for_user():
    location = get_current_location()
    try:
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

def get_calendar_service():
    creds = None
    token_path = 'token.json'
    credentials_path = 'scheduler_subsystem/Credentials.json'

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"Arquivo '{credentials_path}' não encontrado. "
                    "Verifique se o seu Credentials.json está na pasta scheduler_subsystem/."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v1', credentials=creds)

def get_today_events():
    try:
        service = get_calendar_service()
        now = datetime.datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    except Exception as e:
        print(f"Erro ao aceder ao Google Calendar: {e}")
        return []

def main():
    print("Testando o subsistema da Moonlight...\n")
    
    print("A verificar localização e clima...")
    location, weather = get_weather_for_user()
    print(f"-> Localização detetada: {location}")
    print(f"-> Clima atual: {weather}\n")
    
    print("A aceder ao Google Calendar...")
    events = get_today_events()
    
    if not events:
        print("-> Nenhum compromisso encontrado para hoje.")
    else:
        print(f"-> Encontrados {len(events)} compromisso(s) para hoje:")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'Sem título')
            print(f"   • [{start}] {summary}")

if __name__ == "__main__":
    main()