from apscheduler.schedulers.blocking import BlockingScheduler
import time

sched = BlockingScheduler()

@sched.scheduled_job('interval', seconds=10)
def timed_job():
    print('This job is run every 10 seconds.')
    print(time.time())


@sched.scheduled_job('cron', second='10, 15, 35, 45')
def scheduled_job():
    print('This job will run every 10 and 15, 35, 45 seconds past the miinute')

#sched.configure(options_from_ini_file)
sched.start()
'''
schedule: 
run main program every second
this means gotta change the button delay to about 0.5 s

run buton check every 0.2 s 


run the update program every 15 minutes?
'0, 15, 30, 45'

oh btw also needs to update the button thing so that if 3 it just turns off the leds
'''

#thanks 
#pip install apscheduler