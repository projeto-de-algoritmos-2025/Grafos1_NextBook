# scripts/get_random_books.py
from django.conf import settings
import requests

def get_random_books(count=12):
    if not hasattr(settings, 'GOOGLE_BOOKS_API_KEY') or not settings.GOOGLE_BOOKS_API_KEY:
        print("Erro: Chave da API não configurada no settings.py")
        return []
    
    try:
        params = {
            'q': 'lang:pt',
            'maxResults': min(count, 40),
            'key': settings.GOOGLE_BOOKS_API_KEY
        }
        
        response = requests.get(
            'https://www.googleapis.com/books/v1/volumes',
            params=params
        )
        
        # Verifica se a resposta foi bem sucedida
        if response.status_code == 200:
            data = response.json()
            return data.get('items', [])[:count]
        else:
            print(f"Erro na API: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"Erro ao acessar a API: {str(e)}")
        return []

