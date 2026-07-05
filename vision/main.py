import time

from vision import run_camera
import serial

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

def main():
    time.sleep(2)

    while True:
        ser.write("pc_start\n".encode())

        # if esp returns esp_ack break loop
        if ser.readline().decode().strip() == "esp_ack":
            break

        time.sleep(0.1)

    run_camera(ser)


if __name__ == "__main__":
    main()
