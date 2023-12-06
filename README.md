# picoclock

The idea is to use a Raspberry Pico board to generate a clock signal that could be directly connected to the PHI2 pin of a 6502 microprocessor.

It is a square wave generator that can generate frequency from 1 Hz to 127 Mhz, the maximum frequency you can get from a Raspberry Pico GPIO pin configured as PWM.

Picoclock will have a four-digit, seven-segment display to inform the user about the current frequency and operational messages.

Picoclock will have six push buttons:

- **Reset**: reset picoclock to the default configuration. The configuration is stored in the `main.py` file.
- **Cycle**: Cycle the first digit from 0 to 9.
- **Shift**: Multiply the current sequence by ten. Combined with the Cycle button, this mechanism will allow you to enter frequencies from 0 to 9999.
- **Set**: This button will configure picoclock with the current displayed frequency and start the clock.
- **Start/Stop**: Start and stop the clock to allow the user to freeze the 6502 in the current state. This will work only if you use a modern 6502 with a fully static design (e.g., W65C02S6TPLG-14 from The Western Design Center, Inc.)
- **Pulse**: Pushing this button will generate a transition from low to high and high to low on the clock output pin. This allows you to single-step the 6502 microprocessor.

I have decided to go with MicroPython since I use Python for most of my projects.

The `main.py` file contains the following configuration:

```
# GPIO pin mapping

PIN_CLOCK = 0                # Output pin for generated clock signal
PIN_BUTTON_RESET = 16.       # Reset button
PIN_BUTTON_CYCLE = 17        # Cycle button
PIN_BUTTON_SHIFT = 18        # Shift button
PIN_BUTTON_SET = 19          # Set button
PIN_BUTTON_START_STOP = 20.  # Start/Stop button
PIN_BUTTON_PULSE = 21        # Pulse button
PIN_LED = 25                 # On board led (on if the clock is running)
PIN_DISPLAY_CLK = 2          # i2c CLK Pin (Mapped on i2c1 on Pico)
PIN_DISPLAY_DIO = 3          # i2c DIO Pin (Mapped on i2ci on Pico)
```

You can modify these according to your taste.

```
DEFAULT_CLOCK_FREQUENCY = 1 # Frequency in Hz
DEFAULT_CLOCK_MULTIPLIER = 1 # Multiplier for PWM frequency
```

These are three global variables that declare:
`DEFAULT_CLOCK_FREQUENCY`: The starting frequency value to be displayed and used upon board startup.
`DEFAULT_CLOCK_MULTIPLIER`: When setting or starting and stopping the clock, the clock frequency will be multiplied by the value of this variable.

I use picoclock with a minimal frequency and have always stayed within 1 Mhz. It should work :-).

This is it. I have put this together in an hour or so, and I am no expert at all in circuit design. The Python code is 'quick and dirty' and needs to be optimized.

# Schematics

This is the circuit I have designed. My scarce knowledge of Kicad did not allow me to do any better.
![Picoclock Schematic](https://github.com/dotdust/picoclock/blob/main/pictures/picoclock_schematics.png)
You will find the Kicad files for this "project" in the kicad directory.

# Bill of materials

This is what you will need to build a picoclock:

- One 840 points solderless breadboard. Please buy a high-quality board to avoid issues.
- One Raspberry Pi Pico (SKU:  RPI-PICO).
- Six button switches. Choose some that can fit on the breadboard easily.
- One four-digit 7-segment display with an i2c interface.
- Six 220 ohm resistors.

# Picoclock assembly

The circuit is so simple that you will not need help putting it together. Below is a picture of my final assembly (if you can say "final" to any personal project).

![Picoclock assembled](https://github.com/dotdust/picoclock/blob/main/pictures/picoclock.jpg)

# Software

You will need to set up the Raspberry Pi Pico for MicroPython development. You can find detailed instructions here: [MicroPython](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html)

I have used Visual Studio Code for development and testing. Even if I prefer to work with PyCharm, the Visual Studio Code MicroPython extension is much better than the one you will find on PyCharm. The Visual Studio Code extension I have used is [MicroPico](https://github.com/paulober/MicroPico).

Just upload the project to your Raspberry Pico, and you will be ready.

### Development note

While writing the software, I discovered that the Pico PWM can not generate frequencies below 8 Hz. This is why I had to use PWM for frequencies greater than 10 Hz and a Timer for frequencies below or equal to 10 Hz.  Interestingly enough, I did not have the same problem using a Raspberry Pi Model 3b.

# Final words

This project is not up to par with others built by much more experienced people out there. It is something that works for me and that I wanted to share.

It is also expensive compared to other square wave generators you can build or buy. I always use these kind of projects to learn something.
