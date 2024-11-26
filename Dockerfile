FROM ghcr.io/osgeo/gdal:ubuntu-full-latest

RUN apt-get update
RUN apt-get -y install python3-pip git --fix-missing

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements