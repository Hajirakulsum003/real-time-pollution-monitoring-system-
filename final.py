import spidev
import os
import time
import Adafruit_DHT  # DHT11 sensor librar
import BlynkLib
from twilio.rest import Client# Blynk library for sending data to Blynk

# Blynk Setup
BLYNK_AUTH_TOKEN = 'Rz33pDJatTpjKuAh7xAdyTQ7Mt4uOMyX'  # Replace with your Blynk Auth Token
blynk = BlynkLib.Blynk(BLYNK_AUTH_TOKEN)

# Twilio Setup
TWILIO_ACCOUNT_SID = 'AC9415bc51bbcc86e44e9dfd16664772d7'  # Replace with your Twilio Account SID
TWILIO_AUTH_TOKEN = '07f2f9f47d16014749fa4594a881aaee'  # Replace with your Twilio Auth Token
TWILIO_PHONE_NUMBER = '+17755570954'  # Replace with your Twilio phone number
TO_PHONE_NUMBER = '+919739103335'

# Sensor Channels
mq2_channel = 0  
mq3_channel = 1  
turbidity_channel = 2
soil_moisture_channel = 4  # Assuming soil moisture sensor is connected to channel 4

# Initialize SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # SPI bus 0, device 0
spi.max_speed_hz = 1000000  # SPI clock speed
spi.mode = 0b00  # SPI mode

# Alert text if dangerous gas level detected
text = "Air Quality is 200 PPM Don't Step Out of House"
speed = 120  # Speech speed for text-to-speech output

# DHT11 Sensor Pin (GPIO 21)
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 21  # GPIO pin number where the DHT11 sensor is connected

# Send SMS using Twilio
def send_sms_alert():
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=text,
        from_=TWILIO_PHONE_NUMBER,
        to=TO_PHONE_NUMBER
    )
    print(f"Alert sent: {message.sid}")



# Function to read ADC values
def read_adc(channel):
    if channel < 0 or channel > 7:
        raise ValueError("ADC channel must be between 0 and 7")
    
    response = spi.xfer2([1, (8 + channel) << 4, 0])  # SPI transfer
    adc_value = ((response[1] & 3) << 8) + response[2]  # Combine response bytes
    return adc_value

# Read gas sensors (MQ2 and MQ3)
def read_mq2():
    return read_adc(mq2_channel)

def read_mq3():
    return read_adc(mq3_channel)

# Read turbidity sensor
def read_turbidity():
    return read_adc(turbidity_channel)

# Read soil moisture sensor
def read_soil_moisture():
    return read_adc(soil_moisture_channel)

# Read DHT11 sensor (temperature and humidity)
def read_dht11():
    humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
    if humidity is not None and temperature is not None:
        return temperature, humidity
    else:
        print("Failed to read DHT11 sensor")
        return None, None

# Main function
def main():
    try:
        print("Reading sensors data...")
        while True:
            # Read gas sensor values
            gas_value = read_mq2()
            print(f"Gas Sensor ADC Value: {gas_value}")
            # Send gas data to Blynk (virtual pin V1)
            blynk.virtual_write(1, gas_value)
            time.sleep(1)  
            
            gas_value1 = read_mq3()
            print(f"CO Sensor ADC Value: {gas_value1}")
            # Send CO sensor data to Blynk (virtual pin V2)
            blynk.virtual_write(2, gas_value1)
            time.sleep(1)

            # Read turbidity sensor value
            turbidity_value = read_turbidity()
            print(f"Turbidity Sensor ADC Value: {turbidity_value}")
            # Send turbidity data to Blynk (virtual pin V3)
            blynk.virtual_write(3, turbidity_value)
            time.sleep(1)

            # Read soil moisture sensor value
            soil_moisture_value = read_soil_moisture()
            print(f"Soil Moisture Sensor ADC Value: {soil_moisture_value}")
            # Send soil moisture data to Blynk (virtual pin V4)
            blynk.virtual_write(4, soil_moisture_value)
            time.sleep(1)

            # Read DHT11 sensor (temperature and humidity)
            temperature, humidity = read_dht11()
            if temperature is not None and humidity is not None:
                print(f"DHT11 Sensor - Temperature: {temperature}°C, Humidity: {humidity}%")
                # Send temperature and humidity to Blynk (virtual pins V5 and V6)
                blynk.virtual_write(5, temperature)
                blynk.virtual_write(6, humidity)
            time.sleep(1)
            
            # Check if gas value exceeds threshold (example: 435)
            if gas_value > 195:
                os.system(f"espeak-ng -v en+f3 -s {speed} \"{text}\"")
                send_sms_alert()

            # Soil moisture level check (example threshold: 500)
            if soil_moisture_value < 500:  # Example threshold: below 500 indicates dry soil
                print("Warning: Soil moisture is low! Consider watering the plants.")
            
            # Example of warning if temperature is above 30°C
            if temperature is not None and temperature > 30:
                print("Warning: High temperature detected!")

            # Example of warning if humidity is below 20%
            if humidity is not None and humidity < 20:
                print("Warning: Low humidity detected!")

            # Call Blynk.run() to handle Blynk communication
            blynk.run()

    except KeyboardInterrupt:
        print("Program interrupted.")
    finally:
        spi.close()  # Ensure SPI connection is closed

if __name__ == "__main__":
    main()



