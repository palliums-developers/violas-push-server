FROM ubuntu

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install python3 python3-pip git

COPY . /violas-push-server
RUN pip3 install -r /violas-push-server/requirements.txt

WORKDIR /violas-push-server

EXPOSE 4006
CMD ["gunicorn", "-b", "127.0.0.1:4006", "-w", "4", "ViolasPushServer:app"]
