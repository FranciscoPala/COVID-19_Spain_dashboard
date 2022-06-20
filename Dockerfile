FROM python:3.8.13

WORKDIR /src
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

EXPOSE 8501

COPY data /src/data
COPY app.py /src/app.py
COPY .streamlit /src/.streamlit
COPY utils/funcs.py /src/utils/funcs.py

ENTRYPOINT [ "streamlit", "run" ]
CMD ["app.py"]
