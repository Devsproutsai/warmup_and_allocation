FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt 

COPY warmup_allocation.py /code/

EXPOSE 8000

CMD ["uvicorn", "warmup_allocation:app", "--host=0.0.0.0", "--port=8000"]