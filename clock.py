from apscheduler.schedulers.blocking import BlockingScheduler
from DataTable import Users
from app2 import clock_message
import requests
from Setting import URL

sched = BlockingScheduler()
sched_req = BlockingScheduler()
user = Users()


@sched.scheduled_job('interval', minutes=1)
def time_job():
    requests.get(URL)
    users = user.get_reminder()
    if users != -1:
        for us in users:
            clock_message(us)


sched.start()
sched_req.start()
