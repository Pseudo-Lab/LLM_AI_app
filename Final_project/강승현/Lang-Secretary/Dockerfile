FROM python:3.11-slim

WORKDIR /src

# requirements + 코드 복사
COPY . .

# 권한 부여
RUN chmod +x run.sh

# 설치
RUN pip install -r requirements.txt

CMD ["bash", "run.sh"]