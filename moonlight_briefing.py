import os
import datetime
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_current_location():
    try:
        response = requests.get("https://ipapi.co/json/", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return f"{data.get('city', 'Brasília')}, {data.get('country_name', 'Brazil')}"
    except Exception:
        pass
    return "Brasília, Brazil"

def get_weather_for_user():
    location = get_current_location()
    try:
        url = f"https://wttr.in/{location.replace(' ', '+')}?format=j1"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            current = response.json()['current_condition'][0]
            return location, f"{current['temp_C']}°C com {current['weatherDesc'][0]['value'].lower()}"
    except Exception:
        pass
    return location, "clima indisponível"

def get_calendar_service():
    creds = None
    token_path = 'scheduler_subsystem/token.json'
    credentials_path = 'scheduler_subsystem/Credentials.json'

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"Arquivo '{credentials_path}' não encontrado.")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

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

def gerar_briefing():
    print("A iniciar o briefing diário da Moonlight...\n")
    
    # Obter clima e localização
    location, weather = get_weather_for_user()
    
    # Obter eventos
    events = get_today_events()
    
    # Montar a mensagem de resumo
    saudacao = "Olá Arthur! Aqui está o teu resumo para hoje."
    clima_texto = f"Atualmente em {location}, faz {weather}."
    
    print(saudacao)
    print(clima_texto)
    
    if not events:
        print("Não tens nenhum compromisso agendado para o resto do dia no teu calendário.")
    else:
        print(f"Tens {len(events)} compromisso(s) para hoje:")
        for event in events:
            start_time = event['start'].get('dateTime', event['start'].get('date'))
            # Formatar a hora de forma mais legível se for datetime completo
            if 'T' in start_time:
                hora = start_time.split('T')[1][:5]
                print(f"  • Às {hora} - {event.get('summary', 'Sem título')}")
            else:
                print(f"  • Todo o dia - {event.get('summary', 'Sem título')}")

if __name__ == "__main__":
    gerar_briefing()