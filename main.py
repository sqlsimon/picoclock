from machine import Pin, Timer, PWM
import utime
from time import sleep
import digits.tm1637

version__ = "0.1.0"
debug= True  # Set to False to disable debug messages via the serial port

# GPIO pin mapping
PIN_CLOCK = 0
PIN_BUTTON_RESET = 16
PIN_BUTTON_CYCLE = 17
PIN_BUTTON_SHIFT = 18
PIN_BUTTON_SET = 19
PIN_BUTTON_START_STOP = 20
PIN_BUTTON_PULSE = 21
PIN_LED = 25
PIN_DISPLAY_CLK = 2
PIN_DISPLAY_DIO = 3

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
        self.button_cycle = Pin(PIN_BUTTON_CYCLE, Pin.IN, Pin.PULL_DOWN)
        self.button_shift = Pin(PIN_BUTTON_SHIFT, Pin.IN, Pin.PULL_DOWN)
        self.button_set = Pin(PIN_BUTTON_SET, Pin.IN, Pin.PULL_DOWN)
        self.button_start_stop = Pin(PIN_BUTTON_START_STOP, Pin.IN, Pin.PULL_DOWN)
        self.button_pulse = Pin(PIN_BUTTON_PULSE, Pin.IN, Pin.PULL_DOWN)
        self.onboard_led = Pin(PIN_LED, Pin.OUT)

        # Initialize Interrupts handlers
        self.button_reset.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed_handler)
        self.button_cycle.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed_handler)
        self.button_shift.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed_handler)
        self.button_set.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed_handler)
        self.button_start_stop.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed_handler)
        self.button_pulse.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed_handler)

        # Initialize Display
        self.display = digits.tm1637.TM1637(clk=Pin(PIN_DISPLAY_CLK), dio=Pin(PIN_DISPLAY_DIO))
        self.display.brightness(3)
        self.display.show("Helo")
        sleep(3)
        self.display.number(self.clock_frequency)

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
                    self.display.show("Rst ")
                    sleep(2)
                    self.display.number(self.clock_frequency)
                    self.onboard_led.off()
            elif str(PIN_BUTTON_CYCLE) in str(pin):
                if debug: print("Cycle button pressed")
                frequency = self.clock_frequency * DEFAULT_CLOCK_MULTIPLIER
                if frequency > MAXIMUM_PWM_FREQUENCY:
                    self.display.show("Err ")
                    sleep(3)
                    return
                if self.clock_running:
                    if debug: print("Can't cycle while clock is running")
                else:
                    digit = int(str(self.clock_frequency)[-1])
                    digit += 1
                    if digit >= 10:
                        digit = 1
                    self.clock_frequency = int(str(self.clock_frequency)[:-1] + str(digit))
                    self.display.number(self.clock_frequency)
            elif str(PIN_BUTTON_SHIFT) in str(pin):
                if debug: print("Shift button pressed")
                frequency = self.clock_frequency * DEFAULT_CLOCK_MULTIPLIER
                if frequency > MAXIMUM_PWM_FREQUENCY:
                    self.display.show("Err ")
                    sleep(3)
                    return
                if self.clock_running:
                    if debug: print("Can't shift while clock is running")
                else:
                    if not self.clock_frequency > 999:
                        self.clock_frequency *= 10
                    self.display.number(self.clock_frequency)
            elif str(PIN_BUTTON_SET) in str(pin):
                if debug: print("Set button pressed")
                if self.clock_running:
                    if debug: print("Can't set while clock is running")
                else:
                    frequency = self.clock_frequency * DEFAULT_CLOCK_MULTIPLIER
                    if frequency > MAXIMUM_PWM_FREQUENCY:
                        self.display.show("Err ")
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
                    self.display.show("Run ")
                    sleep(2)
                print("Set button pressed")
            elif str(PIN_BUTTON_START_STOP) in str(pin):
                if debug: print("Start/Stop button pressed")
                if not self.clock_running:
                    if debug: print("Clock started")
                    self.clock_running = True
                    frequency = self.clock_frequency * DEFAULT_CLOCK_MULTIPLIER
                    if frequency > MAXIMUM_PWM_FREQUENCY:
                        self.display.show("Err ")
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
                    self.display.show("Run ")
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
                    self.display.show("Stop")
                    sleep(2)
                    self.display.number(self.clock_frequency)
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


if __name__ == "__main__":
    clock = PicoClock()
    while True:
        sleep(1)
