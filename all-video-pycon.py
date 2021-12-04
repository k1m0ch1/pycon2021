import requests
import wget
from bs4 import BeautifulSoup

STAGES = ["Main Stage", "PyCon Pod 1", "PyCon Pod 2", "PyCon Pod 3", "PyCon Pod 4", "PyCon Pod 5"]

HEADERS = {
  "accesstoken": "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6InlhaHlhLmtpbW9jaGlAZ21haWwuY29tIiwiX2lkIjoiNjE5YTZiYTAzYzViOTkyMzlhMGRiYzgwIiwidXNlcl9pZCI6IjI1MzE5MDciLCJkZXZpY2VfdHlwZSI6IldFQiIsInRpbWVTdGFtcCI6MTYzODU4NDM0NTUxMH0.7zf7EafHEO-zMU1ca6MLrhiWbezSGzdD9qmExRpRFKs",
  "apikey": "96d1502b651eb45a7d594938ad582fd8",
  "content-type": "application/json;charset=UTF-8",
  "devicetype": "WEB",
  "eventid": "8400",
  "organiserid": "1509396",
  "origin": "https://pyconid2021.hubilo.com",
  "referer": "https://pyconid2021.hubilo.com/community/",
  "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
  "source": "COMMUNITY"
}

dataSpeaker = []

getSpeaker = requests.post("https://pyconid2021.hubilo.com/api/v1/app/agenda_time_list", headers=HEADERS)

data = getSpeaker.json()['data']['agenda']

for stage in data:
  for event in stage:

    stream_yard_link = event['agendaInfo']['stream_recording_link'].split("/")[-1]
    linkVid = requests.get(f"https://embed.streamyard.com/{stream_yard_link}")

    parser = BeautifulSoup(linkVid.text, 'html.parser')

    getVid = parser.find("video", {"id": "video-player-tag"})

    dataSpeaker.append({
      "title": event['title'],
      "description": event['agendaInfo']['description'],
      "name": event['agendaInfo']['name'],
      "track_name": event['agendaInfo']['track_name'],
      "stream_recording_link": stream_yard_link,
      "link_video": getVid.get("src")
    })

    print(f"Start Download {event['title']}")

    wget.download(getVid.get("src"), f'./{event["title"]}.mp4')

print(dataSpeaker)
