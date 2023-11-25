import machine
import utime
import network
import urequests


global e
e = 0
#defining gpio
TMP36 = machine.ADC(27)
pulse = machine.ADC(26)
button = machine.Pin(16,machine.Pin.IN, machine.Pin.PULL_DOWN)
led = machine.Pin(15,machine.Pin.OUT)

#setting up network variables
ssid = "TakuSean2"
password = "# tag wifi"
url = "https://sheetdb.io/api/v1/2pl1qf5exp29h"
temp_url = "https://elderly-health-api.vercel.app/api/temperature/addTemperatureReadings"
pulse_url = "https://elderly-health-api.vercel.app/api/pulse/addPulseRateReadings"
emergency_url = "https://elderly-health-api.vercel.app/api/emergencyAlert"


# function to connect to WLAN
def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print("Waiting for connection")
        utime.sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    
def temp_measurement():
    temp_list = [0]
    for i in range(5):
        temp_reading = TMP36.read_u16()
        volt = (3.3/65535)*temp_reading
        real_temp = (100*volt)-50 # converting the reading from raw to temperature 
        temp_list.append(real_temp)
    average_temp = sum(temp_list) // 5
    return average_temp
    temp_list = [0]

def pulse_measurement():
    beat = False
    beats = 0
    bpm = 0
    holder = []
    pulse_signal = []
    start_time = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), start_time) < 10000:
        reading = pulse.read_u16() // 5
        pulse_signal.append(reading)
        print(reading)
        utime.sleep(0.1)
    for i in pulse_signal:
        holder.append(i)
        holder = holder[-10:]
        minima, maxima = min(holder), max(holder)
        max_threshold = (0.65 *(maxima-minima) + minima) 
        min_threshold = (0.5 *(maxima-minima) + minima)
        if i > max_threshold and beat == False:
            beat = True
            beats += 1
        if i < min_threshold and beat == True :
            beat = False
    bpm = beats * 6
    holder = []
    pulse_signal = []
    return bpm
    
def do_it():
    global e
    p = pulse_measurement()
    t = temp_measurement()
    print(int(p))
    utime.sleep(2)
    temp_data = { 'ID' : "Metro1",
          'temp' :  t,
          'msg' : "routine",
          'category' : "Temperature",
        }
    pulse_data = { 'ID' : "Metro1",
          'pulse' : p,
          'msg' : "routine",
          'category' : "Pulse",
        }
    t_response = urequests.post(temp_url, json= temp_data)
    p_response = urequests.post(pulse_url, json= pulse_data)
    print(str(t_response.status_code))
    print(str(p_response.status_code))
    if t_response.status_code == 201 and p_response.status_code == 201 :
        led.value(1)
        utime.sleep(0.5)
        led.value(0)
        utime.sleep(0.5)
        led.value(1)
        utime.sleep(0.5)
        led.value(0)
    else:
        print("Unsucessful")
    temp_data.clear()
    pulse_data.clear()
    
    
def post_and_measure():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected() == False:
        connect()
        do_it()
    else:
        do_it()
        
def emergency(b):
    led.value(1)
    utime.sleep(1)
    led.value(0)
    e_data = { 'ID' : "Metro1",
          'pulse' : p,
          'msg' : "emergency",
          'category' : "Pulse",
        }
    e_response = urequests.post(emergency_url, json= e_data)
    print(str(e_response.status_code))
    if e_response.status_code == 201 :
        led.value(1)
        utime.sleep(0.5)
        led.value(0)
        utime.sleep(0.5)
        led.value(1)
        utime.sleep(0.5)
        led.value(0)
    else:
        print("Unsucessful")
    e_data.clear()
    
    
def main_code():
    led.value(1)
    utime.sleep(0.5)
    led.value(0)
    utime.sleep(0.5)
    led.value(1)
    utime.sleep(0.5)
    led.value(0)
    button.irq(trigger=button.IRQ_RISING, handler=emergency)
    connect()
    while True:
        print("kugona")
        utime.sleep(60)
        print("measuring")
        utime.sleep(1)
        post_and_measure()
    

try:
    main_code()
except KeyboardInterrupt:
    machine.reset()
    wlan.disconnect()
except OSError as e:
    if e.errno == 12:
        # Handle ENOMEM error
        print("Out of memory error encountered. Handling and continuing...")
        # Log the error
        print("Out of memory error. Retrying in 5 seconds...")
        utime.sleep(5)
        post_and_measure()
        



