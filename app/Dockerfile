# Usa una imagen base de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requisitos e instálalos
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn python-multipart

# Copia el código de la aplicación
COPY . /app

# Expone el puerto en el que la aplicación escuchará
EXPOSE 5000

# # Comando para ejecutar la aplicación
# CMD ["python3", "main.py"]

# Comando para ejecutar la aplicación con auto-recarga
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]