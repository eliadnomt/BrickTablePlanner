FROM python:3.13
RUN apt-get update && apt-get install -y git
RUN git clone https://github.com/lpauloin/BrickTablePlanner/
RUN pip3 install -r requiremets.txt
CMD ["python3", "main.py"]
