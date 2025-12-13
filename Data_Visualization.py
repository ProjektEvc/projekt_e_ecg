import serial

# Replace COM3 with your actual port
ser = serial.Serial('COM5', 115200, bytesize=8, parity='N', stopbits=1, timeout=1)

while True:
    data = ser.read(64)  # 32 samples x 2 bytes
    if len(data) == 64:
        samples = []
        for i in range(0, 64, 2):
            # LSB + MSB
            sample = data[i] | (data[i+1] << 8)
            samples.append(sample)
        print(samples)
