import os
import glob
import RPi.GPIO as GPIO
import time
from darksky.api import DarkSky, DarkSkyAsync
from darksky.types import languages, units, weather

SDI   = 17
RCLK  = 18
SRCLK = 27
ButtonPin = 25


class TemperatureHandler:
    """
    Class used to handle grabbing of Temperatures and Weather Data
    Uses Temperature Probe and DarkSky API
    """
    def __init__(self):
        self.base_dir = '/sys/bus/w1/devices/'
        self.device_folder = glob.glob(self.base_dir + '28*')[0]
        self.device_file = self.device_folder + '/w1_slave'

        self.API_KEY = 'fe062f8bf0e70e288d3e784f21381ab6'
        self.latitude = 52.449851
        self.longitude = -1.930616

        self.probetemp = 0
        self.forecast = 0

        self.tempflag = 0 #[0 = probe, 1 = DarkSky]
    
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

    def increment_flag(self, u):
        """Public method to increment temperature flag"""
        self.tempflag += u
        self.tempflag = self.tempflag % 2 #update the 2 if more optoins pop up

    def update_flag(self, val):
        """Public method to manually update temperature flag if needed"""
        self.tempflag = val

    def call_temp(self):
        """Returns current temperature, based on current flag"""
        if self.tempflag == 0:
            return self.probetemp
        elif self.tempflag == 1:
            return self.forecast.currently.apparent_temperature

    def call_precip_prob(self):
        return self.forecast.daily.precip_probability

    def call_flag(self):
        return self.tempflag

class LEDHandler:
    """Class that handles lighting up the LEDs"""
    def __init__(self):
        self.SDI   = 17
        self.RCLK  = 18
        self.SRCLK = 27

        GPIO.setmode(GPIO.BCM)    # Number GPIOs by BCM
        GPIO.setwarnings(False)
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

class ButtonHandler:
    """Class that handles buttons. Paired with a TemperatureHandler object"""
    def __init__(self, TempHandler):
        self.ButtonPin = 25
        GPIO.setup(ButtonPin, GPIO.IN)
        
        self.paired = TempHandler

    def checkinput(self):
        """
        Checks if button is pressed or not
        If pressed, increments flag in the paired TemperatureHandler object"""
        if GPIO.input(self.ButtonPin) == False:
            self.paired.increment_flag(1)
            time.sleep(0.5)





temp_obj = TemperatureHandler()
LED_obj = LEDHandler()
but_obj =  ButtonHandler(temp_obj)

#run every 0.2s
def buttoncheck(self):
    but_obj.checkinput()

#run every second
def displaytemp():
    temp_obj.update_probetemp()

    blue_light_bin = 0b00100000
    red_light_bin  = 0b01000000


    current_temp = int(temp_obj.call_temp())
    if current_temp < 0:
        current_temp = 0 
    elif current_temp > 31:
        current_temp = 31

    precip_flag = 0
    if temp_obj.call_precip_prob() >= 0.5: #gotta modify chance after u do the testings
        precip_flag = 1
    






if __name__ == '__main__':
    """
    TODO:
    - combine all the classes together somehow
    - make it so that they talk to each other and all that jazz
    - make a readme
    """


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