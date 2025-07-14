import socket
import network
import time
from machine import Pin

# === Setup LED ===
led = Pin(2, Pin.OUT)  # Built-in LED (D2 on most ESP32 boards)

def blink(times, interval_ms=200):
    for _ in range(times):
        led.value(1)
        time.sleep_ms(interval_ms)
        led.value(0)
        time.sleep_ms(interval_ms)

# === Connect to Wi-Fi ===
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("Teman Kenangan")  # Open network (no password)

print("Connecting to Wi-Fi...")
timeout = time.ticks_ms()
while not wlan.isconnected():
    if time.ticks_diff(time.ticks_ms(), timeout) > 10000:  # 10s timeout
        print("Wi-Fi connection failed.")
        led.value(0)
        raise OSError("Wi-Fi connect timeout")
    time.sleep(0.1)

print("Connected to Wi-Fi:", wlan.ifconfig())
blink(1)  # 1x blink for Wi-Fi connected
time.sleep(2)  # Delay before TCP

# === Setup TCP Connection ===
HOST = '192.168.110.191'  # Replace with your PC IP
PORT = 12345

s = socket.socket()
try:
    s.connect((HOST, PORT))
    s.send(b"esp\n")  # Identify as ESP32 client
    print("TCP connected")
    blink(3)  # 3x blink for TCP connected
except Exception as e:
    print("TCP connection failed:", e)
    led.value(0)
    raise e

# === Main Loop ===
zone_c_active = False
last_blink = time.ticks_ms()
led_state = False

while True:
    # Non-blocking receive
    s.settimeout(0.1)
    try:
        data = s.recv(1024)
        if data:
            text = data.decode().strip()
            print("[ESP] Received:", text)
            zone_c_active = "zone_c=1" in text
    except:
        pass

    # Blink continuously at 3Hz if zone_c is active
    if zone_c_active:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_blink) >= 167:  # ~3Hz
            led_state = not led_state
            led.value(led_state)
            last_blink = now
    else:
        led.value(0)
        led_state = False
