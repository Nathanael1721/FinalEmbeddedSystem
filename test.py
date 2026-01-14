from machine import Pin, PWM
import time

# ===== PIN SETUP =====
TRIG_PIN = 14
ECHO_PIN = 15
SERVO_PIN = 16

trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)

servo = PWM(Pin(SERVO_PIN))
servo.freq(50)  # Servo standar 50Hz

# ===== FUNGSI SERVO =====
def set_servo_angle(angle):
    # Konversi sudut ke duty (0-180)
    min_duty = 1638   # ~0.5 ms
    max_duty = 8192   # ~2.5 ms
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    servo.duty_u16(duty)

# ===== FUNGSI ULTRASONIK =====
def get_distance():
    trig.low()
    time.sleep_us(2)
    trig.high()
    time.sleep_us(10)
    trig.low()

    while echo.value() == 0:
        pulse_start = time.ticks_us()

    while echo.value() == 1:
        pulse_end = time.ticks_us()

    pulse_duration = time.ticks_diff(pulse_end, pulse_start)
    distance = (pulse_duration * 0.0343) / 2
    return distance

# ===== LOOP UTAMA =====
while True:
    for angle in [0, 90, 180]:
        set_servo_angle(angle)
        time.sleep(0.5)

        distance = get_distance()
        print("Servo:", angle, "° | Jarak:", distance, "cm")

    print("-----")
    time.sleep(1)
