import os
import glob
import RPi.GPIO as GPIO
import time
from darksky.api import DarkSky, DarkSkyAsync
from darksky.types import languages, units, weather
#from apscheduler.schedulers.blocking import BlockingScheduler



class ButtonHandler:
    """Class that handles buttons. Paired with a TemperatureHandler object"""
    def __init__(self):
        self.ButtonPin = 25
        GPIO.setup(self.ButtonPin, GPIO.IN)
        self.buttonstate = 0

        #button states
        #0 = off
        #1 = probe
        #2 = darksky

    def checkinput(self):
        """
        Checks if button is pressed or not
        If pressed, increments flag in the paired TemperatureHandler object"""
        if GPIO.input(self.ButtonPin) == False:
            self.buttonstate += 1
            self.buttonstate = self.buttonstate % 3 #update modulus if more options pop up
            time.sleep(0.5)

    def call_state(self):
        """Public method returning the current buttonstate"""
        return self.buttonstate

class TemperatureHandler:
    """
    Class used to handle grabbing of Temperatures and Weather Data
    Uses Temperature Probe and DarkSky API
    """
    def __init__(self, pairedbutton):
        self.base_dir = '/sys/bus/w1/devices/'
        self.device_folder = glob.glob(self.base_dir + '28*')[0]
        self.device_file = self.device_folder + '/w1_slave'

        self.API_KEY = 'fe062f8bf0e70e288d3e784f21381ab6'
        self.latitude = 52.449851
        self.longitude = -1.930616

        self.probetemp = 0
        self.forecast = 0

        self.probeflag = True

        self.pairedbutton = pairedbutton
    
    def _probe_temp_raw(self):
        """Reads the raw data file from the probe"""
        f = open(self.device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines
    
    def _probe_temp(self):
        """Converts raw data file into celsius"""
        lines = self._probe_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self._probe_temp_raw()
        
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c

    def _darksky_forecast(self):
        """
        Grabs forcast from DarkSky API
        Returns Forecast (see their documentation)
        """
        darksky = DarkSky(self.API_KEY)
        forecast = darksky.get_forecast(
            self.latitude, self.longitude,
            extend=False, # default `False`
            lang=languages.ENGLISH, # default `ENGLISH`
            exclude=[weather.MINUTELY, weather.ALERTS], # default `[]`,
            timezone='UTC' # default None - will be set by DarkSky API automatically
        )
        return forecast

    def update_darksky(self):
        """Updates forecast, used to limit calls to their API due to 1000 limit"""
        self.forecast = self._darksky_forecast()

    def update_probetemp(self):
        """Public method to access probe's temp"""
        self.probetemp = self._probe_temp()

    def update_flag(self, boolean):
        """Public method to manually update temperature flag if needed"""
        self.probeflag = boolean

    def call_temp(self):
        """Returns current temperature, based on current flag"""
        if self.pairedbutton.call_state() == 1:
            self.probeflag = True
        elif self.pairedbutton.call_state() == 2:
            self.probeflag = False

        if self.probeflag == True:
            return self.probetemp
        elif self.probeflag == False:
            return self.forecast.currently.apparent_temperature

    def call_precip_prob(self):
        """public method returning precip prob of today"""
        return self.forecast.daily.data[0].precip_probability

    def call_probeflag(self):
        """public method returning probe flag value"""
        return self.probeflag
    
    def call_alerts(self):
        """public method returning any DarkSky Alerts"""
        return self.forecast.alerts

class LEDHandler:
    """Class that handles lighting up the LEDs"""
    def __init__(self):
        self.SDI   = 17
        self.RCLK  = 18
        self.SRCLK = 27

        GPIO.setup(self.SDI, GPIO.OUT)
        GPIO.setup(self.RCLK, GPIO.OUT)
        GPIO.setup(self.SRCLK, GPIO.OUT)
        GPIO.output(self.SDI, GPIO.LOW)
        GPIO.output(self.RCLK, GPIO.LOW)
        GPIO.output(self.SRCLK, GPIO.LOW)

    def _hc595_in(self, dat):
        """Input to the shiftregister"""
        for bit in range(0, 8):
            GPIO.output(self.SDI, 0x80 & (dat << bit))
            GPIO.output(self.SRCLK, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(self.SRCLK, GPIO.LOW)
    
    def _hc595_out(self):
        """Outputs the shiftregister"""
        GPIO.output(self.RCLK, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.RCLK, GPIO.LOW)
    
    def lightup(self, dat):
        """
        Public method to light up the LEDs. 
        dat is number in binary that says which light is on
        """
        self._hc595_in(dat)
        self._hc595_out()

#sched = BlockingScheduler()

GPIO.setmode(GPIO.BCM)    # Number GPIOs by BCM
GPIO.setwarnings(False)

but_obj =  ButtonHandler()
temp_obj = TemperatureHandler(but_obj)
LED_obj = LEDHandler()

temp_obj.update_darksky()




#@sched.scheduled_job('interval', seconds=1)
def buttoncheck():
    but_obj.checkinput()

#@sched.scheduled_job('cron', second='10, 15, 35, 45')
def updateforecast():
    temp_obj.update_darksky()

#run every second
def displaytemp():
    """ updates and displays current temperatures """
    temp_obj.update_probetemp()

    if but_obj.call_state() == 0:
        LED_obj.lightup(0)
        return


    blue_light_bin   = 0b00100000
    red_light_bin    = 0b01000000
    alerts_light_bin = 0b10000000


    current_temp = int(temp_obj.call_temp())
    if current_temp < 0:
        current_temp = 0 
    elif current_temp > 31:
        current_temp = 31

    precip_flag = 0
    if temp_obj.call_precip_prob() >= 0.5: #gotta modify chance after u do the testings
        precip_flag = 1

    redprobe_flag = 0
    if temp_obj.call_probeflag() == False:
        redprobe_flag = 1
    
    alerts_flag = 0
    if len(temp_obj.call_alerts()) != 0:
        alerts_flag = 1
    
    data = current_temp + (precip_flag * (blue_light_bin) 
                        + redprobe_flag * red_light_bin
                        + alerts_flag * alerts_light_bin)
     

    LED_obj.lightup(data)



if __name__ == '__main__':
    """
    TODO:
    - add scheduler (lines 7, 164, and comments above functions)
    - make a readme
    """


    displaytemp()

    start = time.time()
    fin = time.time()
    print(temp_obj.call_temp())
    while fin-start < 10:
        fin = time.time()
        displaytemp()
    
    '''
    lighttest = LEDHandler()
    lighttest.lightup(0x00)
    GPIO.cleanup()
    '''
    
    '''
    try:
        Do the job
    except KeyboardInterrupt
        stop the job from ap scheduler
    '''
    
    
    """
    #include testing stuffs here
    temptest = TemperatureHandler()
    #print(test.call_temp())
    print(temptest.call_temp())
    temptest.update_probetemp()
    print(temptest.call_temp())



    buttest = ButtonHandler(temptest)
    print('buttontestphase')
    starttime = time.time()
    finishtime = time.time()
    while finishtime-starttime < 10:
        finishtime = time.time()
        buttest.checkinput()
        print(temptest.tempflag)

    



    test.update_darksky()
    print(test.forecast.currently.apparent_temperature)
    print(test.forecast.currently.precip_probability) 
    """