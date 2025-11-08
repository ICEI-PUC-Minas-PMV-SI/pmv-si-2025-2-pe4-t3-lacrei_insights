FROM python:3.10

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Copia todos os arquivos do projeto local para dentro do container
COPY . .

# Define a raiz do Python para reconhecer imports relativos a partir da pasta /app
ENV PYTHONPATH=/app

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta da aplicação
EXPOSE 5000

# Comando de execução
CMD ["python", "run.py"]
