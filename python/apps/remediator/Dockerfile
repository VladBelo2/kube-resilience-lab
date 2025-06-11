FROM python:3.10
WORKDIR /app
COPY remediator.py .
RUN pip install requests prometheus_client kubernetes
CMD ["python", "-u", "remediator.py"]
