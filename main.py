from machine import Pin, Timer, PWM, I2C
import utime
from time import sleep
from rotary_irq_rp2 import RotaryIRQ
from ssd1306 import SSD1306_I2C
import framebuf,sys

version__ = "0.1.0"
debug= True  # Set to False to disable debug messages via the serial port

# GPIO pin mapping 
PIN_CLOCK = 0
PIN_BUTTON_RESET = 16
PIN_BUTTON_SHIFT = 18
PIN_BUTTON_SET = 17
PIN_BUTTON_START_STOP = 20
PIN_BUTTON_PULSE = 21
PIN_LED = 25
PIN_I2C_SDA = 6 # OLED DISPLAY
PIN_I2C_SCL = 7 # OLED DISPLAY
PIN_ROTARY_CLK = 22
PIN_ROTARY_DT = 28 

# Debounce delay in milliseconds
DEBOUNCE_DELAY = 500

DEFAULT_CLOCK_FREQUENCY = 1 # Frequency in Hz
DEFAULT_CLOCK_MULTIPLIER = 1 # Multiplier for PWM frequency
MAXIMUM_PWM_FREQUENCY = 127_000_000 # Maximum PWM frequency in Hz




class PicoClock:
    last_time = 0
    new_time = 0
    clock_frequency = DEFAULT_CLOCK_FREQUENCY
    clock_multiplier = DEFAULT_CLOCK_MULTIPLIER
    clock_running = False
    clock_timer = None
    pwm_clock = None
    display = None
    onboard_led = None

    button_reset, button_cycle, button_shift, button_set, button_start_stop, button_pulse = \
        None, None, None, None, None, None

 

    def __init__(self):
        # Initialize Pico GPIO pins
        self.pwm_clock = Pin(PIN_CLOCK, Pin.OUT)
        self.button_reset = Pin(PIN_BUTTON_RESET, Pin.IN, Pin.PULL_DOWN)
        self.button_shift = Pin(PIN_BUTTON_SHIFT, Pin.IN, Pin.PULL_DOWN)
        self.button_set = Pin(PIN_BUTTON_SET, Pin.IN, Pin.PULL_DOWN)
        self.button_start_stop = Pin(PIN_BUTTON_START_STOP, Pin.IN, Pin.PULL_DOWN)
        self.button_pulse = Pin(PIN_BUTTON_PULSE, Pin.IN, Pin.PULL_DOWN)
        self.onboard_led = Pin(PIN_LED, Pin.OUT)

        # Initialize Interrupts handlers
        self.button_reset.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed_handler)
        self.button_shift.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed_handler)
        self.button_set.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed_handler)
        self.button_start_stop.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed_handler)
        self.button_pulse.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed_handler)

        sleep(3)
        
        # Initialize SSD1306 Display
        pix_res_x  = 128 # SSD1306 horizontal resolution
        pix_res_y  = 32  # SSD1306 vertical resolution

        i2c_dev = I2C(1,scl=Pin(PIN_I2C_SCL),sda=Pin(PIN_I2C_SDA),freq=200000)  # start I2C on I2C1 (GPIO 26/27)
        i2c_addr = [hex(ii) for ii in i2c_dev.scan()] # get I2C address in hex format
        
        # i2c address = 0x3c
        
        if i2c_addr==[]:
            if debug: print('No I2C Display Found') 
            sys.exit() # exit routine if no dev found
        else:
            if debug: print("I2C Address      : {}".format(i2c_addr[0])) # I2C device address
            if debug: print("I2C Configuration: {}".format(i2c_dev)) # print I2C params

        self.oled = SSD1306_I2C(pix_res_x, pix_res_y, i2c_dev) # oled controller
        
        self.show_message("Pico Clock V1.0")
        

        

  
    def button_pressed_handler(self, pin):
        self.new_time = utime.ticks_ms()
        if (self.new_time - self.last_time) > DEBOUNCE_DELAY:
            if str(PIN_BUTTON_RESET) in str(pin):
                if debug: print("Reset button pressed")
                if self.clock_running:
                    if debug: print("Can't reset while clock is running")
                else:
                    self.clock_running = False
                    self.clock_frequency = DEFAULT_CLOCK_FREQUENCY
                    self.show_message("Reset")
                    sleep(2)
                    self.onboard_led.off()
            elif str(PIN_BUTTON_SHIFT) in str(pin):
                if debug: print("Shift button pressed")
                frequency = self.clock_frequency * DEFAULT_CLOCK_MULTIPLIER
                if frequency > MAXIMUM_PWM_FREQUENCY:
                    self.show_message("Error freq exceeded")
                    sleep(3)
                    return
                if self.clock_running:
                    if debug: print("Can't shift while clock is running")
                else:
                    if not self.clock_frequency > 999:
                        self.clock_frequency *= 10
                    self.show_message("Frequency Changed")
            elif str(PIN_BUTTON_SET) in str(pin):
                if debug: print("Set button pressed")
                if self.clock_running:
                    if debug: print("Can't set while clock is running")
                else:
                    frequency = self.clock_frequency * DEFAULT_CLOCK_MULTIPLIER
                    if frequency > MAXIMUM_PWM_FREQUENCY:
                        self.show_message("Error")
                        sleep(3)
                        return
                    if frequency < 10:
                        self.pwm_clock = Pin(PIN_CLOCK, Pin.OUT)
                        self.clock_timer = Timer()
                        self.clock_timer.init(freq=frequency, mode=Timer.PERIODIC, callback=self.non_pwm_clock)
                    else:
                        self.pwm_clock = PWM(Pin(PIN_CLOCK))
                        self.pwm_clock.freq(frequency)
                        self.pwm_clock.duty_u16(32512)
                    self.onboard_led.on()
                    self.clock_running = True
                    self.show_message("Clock Run")
                    sleep(2)
                print("Set button pressed")
            elif str(PIN_BUTTON_START_STOP) in str(pin):
                if debug: print("Start/Stop button pressed")
                if not self.clock_running:
                    if debug: print("Clock started")
                    self.clock_running = True
                    frequency = self.clock_frequency * DEFAULT_CLOCK_MULTIPLIER
                    if frequency > MAXIMUM_PWM_FREQUENCY:
                        self.show_message("Error")
                        sleep(3)
                        return
                    if frequency < 10:
                        self.pwm_clock = Pin(PIN_CLOCK, Pin.OUT)
                        self.clock_timer = Timer()
                        self.clock_timer.init(freq=frequency, mode=Timer.PERIODIC, callback=self.non_pwm_clock)
                    else:
                        self.pwm_clock = PWM(Pin(PIN_CLOCK))
                        self.pwm_clock.freq(frequency)
                        self.pwm_clock.duty_u16(32512)
                    self.onboard_led.on()
                    self.show_message("Run")
                    sleep(2)
                else:
                    if debug: print("Clock stopped")
                    self.clock_running = False
                    if self.clock_frequency < 10:
                        self.clock_timer.deinit()
                    else:
                        self.pwm_clock = PWM(Pin(PIN_CLOCK))
                        self.pwm_clock.duty_u16(0)
                        self.pwm_clock.deinit()
                    self.onboard_led.off()
                    self.show_message("Stop")
                    sleep(2)
            elif str(PIN_BUTTON_PULSE) in str(pin):
                if debug: print("Pulse button pressed")
                if self.clock_running:
                    if debug: print("Can't pulse while clock is running")
                else:
                    half_period_us = int(1_000_000 / self.clock_frequency / 2)
                    self.pwm_clock.on()
                    self.onboard_led.on()
                    utime.sleep_us(half_period_us)
                    self.pwm_clock.off()
                    self.onboard_led.off()
            self.last_time = self.new_time

    def non_pwm_clock(self, timer):
        half_period_us = int(1_000_000 / self.clock_frequency / 2)
        self.pwm_clock.on()
        utime.sleep_us(half_period_us)
        self.pwm_clock.off()

    def show_message(self,textstr):
        self.display_oled(textstr,5,5,True)
        self.display_oled("Frequency: " + str(self.clock_frequency),5,15,False)   

    def display_oled(self,textstr,x,y,clear_display):
        if clear_display: self.oled.fill(0)
        self.oled.text(textstr,x,y)
        self.oled.show()
        
    def set_frequency(self,freq):
        self.clock_frequency = freq
        self.show_message("set freq")

if __name__ == "__main__":
    clock = PicoClock()

    print("RUNNING");
    
    r = RotaryIRQ(pin_num_clk=PIN_ROTARY_CLK,pin_num_dt=PIN_ROTARY_DT,min_val=0,reverse=False,range_mode=RotaryIRQ.RANGE_UNBOUNDED)  

    val_old = r.value()

    while True:
        # NEED TO STOP THE VALUE GOING BELOW 1 
        val_new = r.value()
        if val_old != val_new:
            val_old = val_new
            clock.set_frequency(val_new)
            print('result =', val_new)
        sleep(1)

