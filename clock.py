from apscheduler.schedulers.blocking import BlockingScheduler
from DataTable import Users
from app2 import clock_message

sched = BlockingScheduler()

user = Users()


@sched.scheduled_job('interval', minutes=1)
def time_job():
    users = user.get_userd_id_last_time_in_30_min()
    if users != None:
        for us in users:
            clock_message(us)


sched.start()
