import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Carrega as variáveis do .env automaticamente
load_dotenv()

# Lê a variável do .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Cria função que retorna a engine
def get_engine():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL não definida no .env")
    return create_engine(DATABASE_URL)
