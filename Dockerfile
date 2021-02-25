# set base image (host OS)
FROM python:3.8

# info
LABEL version="0.03"
LABEL description="Web scraping with Docker"

# set the working directory in the container
WORKDIR /Python Files/slots_web_scrape

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY slots_web_scrape/ .

# command to run on container start
# CMD [ "python", "./scrape.py" ]
CMD [ "python", "./all_markets.py" ]




