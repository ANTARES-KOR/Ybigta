FROM python

WORKDIR /app

RUN pip3 install pandas
RUN pip3 install sklearn
RUN pip3 install nltk
RUN pip3 install boto3
RUN pip3 install python-dotenv

COPY . .

RUN mkdir -p /app/data

CMD ["python3", "tfidf.py"]