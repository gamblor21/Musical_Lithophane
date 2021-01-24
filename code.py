import time
import supervisor
import board
import digitalio
import pulseio
from adafruit_motor import servo
import neopixel
from audiomp3 import MP3Decoder

from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation import helper

from timedsequence import TimedAnimationSequence
from volume import Volume

try:
    from audioio import AudioOut
except ImportError:
    try:
        from audiopwmio import PWMAudioOut as AudioOut
    except ImportError:
        pass  # not always supported by every board!

SERVO_SPEED = 0.07 # speed to rotate the servo at
LED_FLASH_TIME = 30 # how long to flash the arcade button for

# Define buttons
power_switch = digitalio.DigitalInOut(board.D10)
power_switch.direction = digitalio.Direction.INPUT
power_switch.pull = digitalio.Pull.UP

mode_button = digitalio.DigitalInOut(board.D11)
mode_button.direction = digitalio.Direction.INPUT
mode_button.pull = digitalio.Pull.UP

flash_button = digitalio.DigitalInOut(board.D7)
flash_button.direction = digitalio.Direction.INPUT
flash_button.pull = digitalio.Pull.UP

# Define LED on the arcade button
flash_button_led = digitalio.DigitalInOut(board.D12)
flash_button_led.direction = digitalio.Direction.OUTPUT
flash_button_led.value = True

# Set up the servo
lid_servo_pwm = pulseio.PWMOut(board.D9, frequency=50)
lid_servo = servo.ContinuousServo(lid_servo_pwm, min_pulse = 420, max_pulse = 2500)
#lid_servo = servo.ContinuousServo(lid_servo_pwm)
lid_servo.throttle = 0.0

# Set up the neopixels
pixels = neopixel.NeoPixel(board.D5, 28, brightness=1.0, auto_write=False, pixel_order=neopixel.GRBW)
pixels.fill((0,0,0))
pixels.show()
pixel_wing_horizontal = helper.PixelMap.horizontal_lines(
    pixels, 7, 4, helper.horizontal_strip_gridmap(7, alternating=False)
)
pixel_wing_vertical = helper.PixelMap.vertical_lines(
    pixels, 7, 4, helper.horizontal_strip_gridmap(7, alternating=False)
)

# Set up the audio playback
audio = AudioOut(board.A0)
#mp3files = ["dance-mono.mp3"]
mp3files = ["dance-mono.mp3"]
mp3 = open(mp3files[0], "rb")
decoder = MP3Decoder(mp3)

# variable set to True if the switch in the back is off
is_shutdown = False

def Shutdown():
    # Power switch is off so shutdown everything.
    global current_mode
    global is_shutdown
    flash_button_led.value = False
    audio.stop()
    pixels.fill((0,0,0))
    pixels.show()
    lid_servo.throttle = 0.0
    current_mode = MODE_OFF
    is_shutdown = True

led_flick_time = 0  # timer for flashing the arcade button led

def FlashLed():
    # Check if it is time to flash the led on the arcade button.
    global led_flick_time
    if (time.monotonic() - led_flick_time) > 0.2:
        led_flick_time = time.monotonic()
        flash_button_led.value = not flash_button_led.value

# define animation for the arcade button
rainbow = Rainbow(pixel_wing_vertical, speed=0.1, period=2)
rainbow_chase = RainbowChase(pixel_wing_vertical, speed=0.1, size=5, spacing=3)
rchase2 = RainbowChase(pixel_wing_horizontal, speed=0.05, size=3, spacing=1)
rainbow_comet = RainbowComet(pixel_wing_vertical, speed=0.05, tail_length=7, bounce=True)
rcomet2 = RainbowComet(pixel_wing_horizontal, speed=0.05, tail_length=7, bounce=True)
rainbow_sparkle = RainbowSparkle(pixel_wing_vertical, speed=0.1, num_sparkles=15)
solid = Solid(pixels, color=(230,230,255))
clear_sparkle = Sparkle(pixels, speed=0.05, color=(230, 230, 250), num_sparkles=10)
loud = Volume(pixel_wing_vertical, speed=0.1, decoder=decoder, max_volume=350, brightest_color=(150,150,170))

# modes the program can be index
MODE_OFF = 0    # nothing running
MODE_LIGHT = 1  # neopixels lit only
MODE_SPIN = 2   # neopixels lit and servo moving
MODE_MUSIC = 3  # music show is on
MODE_MAX = 3    # only the arcade button will get to MUSIC

###
# Start of main code
###

supervisor.set_rgb_status_brightness(0) # turn the on-board LED off

do_flash_led = True # should we flash the arcade button LED
flash_led_on_time = time.monotonic() # how long has it been flashing

mode_button_ready = True # prevent mode button repeating on same press
last_mode_button_press = 0 # prevent button bounce

current_mode = MODE_OFF # the current mode we are in
new_mode = True # is the mode we are entering new

# Main loop
while True:
    # We are shut down do as little as possible
    # Check this first so we don't respond to anything else while shut down
    if power_switch.value is False:
        if is_shutdown is False:
            Shutdown()

        time.sleep(1.0) # time.sleep should switch to low power mode
        continue
    else:
        if is_shutdown is True:
            flash_led_on_time = time.monotonic()
            do_flash_led = True
            is_shutdown = False

    if do_flash_led:
        FlashLed()  # flash the arcade button led
        if (time.monotonic() - flash_led_on_time) > LED_FLASH_TIME:
            do_flash_led = False
            flash_button_led.value = False

    # Check if the mode button is pressed
    if mode_button.value is False:
        # ensure mode button was let go after less press
        if mode_button_ready is True:
            if (time.monotonic() - last_mode_button_press) > 0.2:
                last_mode_button_press = time.monotonic()
                mode_button_ready = False
                if current_mode is MODE_MUSIC:
                    current_mode = MODE_OFF
                else:
                    current_mode = (current_mode + 1) % MODE_MAX
                new_mode = True
                print("Changing mode " , current_mode)
    else:
        mode_button_ready = True # mode button has been let go

    # Check if the arcade button is pressed
    if flash_button.value is False:
        if current_mode is not MODE_MUSIC:
            print("MODE_MUSIC - Let's go")
            new_mode = True
            current_mode = MODE_MUSIC
            do_flash_led = False
            flash_button_led.value = False

    # take actions based on what mode we are in
    # for most only do something if we changed modes
    if current_mode == MODE_OFF:
        if new_mode is True:
            lid_servo.throttle = 0.0
            pixels.fill((0,0,0))
            pixels.show()
            audio.stop()
            new_mode = False
    elif current_mode == MODE_LIGHT:
        if new_mode is True:
            pixels.fill((100,100,110))
            pixels.show()
            new_mode = False
    elif current_mode == MODE_SPIN:
        if new_mode is True:
            lid_servo.throttle = SERVO_SPEED
            new_mode = False
    elif current_mode == MODE_MUSIC:
        if new_mode is True:
            new_mode = False

            lid_servo.throttle = SERVO_SPEED*4

            decoder.file = open(mp3files[0], "rb")
            audio.play(decoder)

            animations = TimedAnimationSequence(


                solid, 12,
                loud, 20, # 32
                rainbow, 16.5, # 48.5
                rainbow_comet, 14, # 1:02.5 62.5
                rchase2, 36, # 1:38.5 98.5
                rainbow, 16.5, # 1:55 115
                rainbow_comet, 14, # 2:09 129
                loud, 33, # 2:42 162
                clear_sparkle, 16, # 2:58 178
                rcomet2, 14, # 3:12 192
                rainbow_sparkle, 32, # 3:44 224
                rchase2, 16, # 4:00 240
                loud, 37, # 4:37 277
                clear_sparkle, 5,
                solid, 60,

                #rainbow_chase, 5,
                #rchase2, 5,


                auto_clear=True,
                auto_reset=True,
            )
        else:
            animations.animate()
            if audio.playing is False:
                new_mode = True
                current_mode = MODE_OFF
            pass