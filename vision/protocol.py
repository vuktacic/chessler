from dataclasses import dataclass
from queue import Empty, Queue
import threading
import time

import serial

from vision import replace_side


@dataclass(frozen=True)
class SerialLog:
    direction: str
    payload: str


class ProtocolState:
    """Track automatic FEN sends independently from serial transport."""

    def __init__(self):
        self.auto_send_enabled = True
        self.next_side = "w"
        self.last_sent_board = None

    def set_auto_send_enabled(self, enabled):
        self.auto_send_enabled = enabled

    def automatic_command(self, board_fen):
        if not self.auto_send_enabled or board_fen == self.last_sent_board:
            return None
        return self._command_for(board_fen)

    def manual_command(self, board_fen):
        return self._command_for(board_fen)

    def mark_sent(self, board_fen):
        self.last_sent_board = board_fen
        self.next_side = "b" if self.next_side == "w" else "w"

    def _command_for(self, board_fen):
        return f"FEN {replace_side(board_fen, self.next_side)}"


class SerialWorker:
    """Own the serial port and expose queued commands and raw protocol logs."""

    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self._commands = Queue()
        self._logs = Queue()
        self._stop_event = threading.Event()
        self._retry_event = threading.Event()
        self._state_lock = threading.Lock()
        self._connected = False
        self._status = "Disconnected"
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1)

    def retry(self):
        self._retry_event.set()

    def status(self):
        with self._state_lock:
            return self._connected, self._status

    def send(self, command):
        command = command.rstrip("\r\n")
        if not command or not self.status()[0]:
            return False
        self._commands.put(command)
        return True

    def drain_logs(self):
        logs = []
        while True:
            try:
                logs.append(self._logs.get_nowait())
            except Empty:
                return logs

    def _set_status(self, connected, status):
        with self._state_lock:
            self._connected = connected
            self._status = status

    def _log(self, direction, payload):
        if payload:
            self._logs.put(SerialLog(direction, payload))

    def _write(self, connection, command):
        connection.write(f"{command}\n".encode())
        connection.flush()
        self._log("TX", command)

    def _connect(self):
        self._set_status(False, f"Connecting to {self.port}")
        try:
            connection = serial.Serial(self.port, self.baudrate, timeout=0.1)
        except (serial.SerialException, OSError):
            self._set_status(False, f"Disconnected: {self.port}")
            return None

        self._set_status(False, "Waiting for ESP handshake")
        while not self._stop_event.is_set():
            try:
                self._write(connection, "pc_start")
                response = connection.readline().decode(errors="ignore").strip()
            except (serial.SerialException, OSError):
                connection.close()
                self._set_status(False, f"Disconnected: {self.port}")
                return None
            if response:
                self._log("RX", response)
            if response == "esp_ack":
                self._set_status(True, "Connected")
                return connection
            self._stop_event.wait(0.1)

        connection.close()
        return None

    def _run(self):
        connection = None
        next_attempt = 0.0
        try:
            while not self._stop_event.is_set():
                if connection is None:
                    now = time.monotonic()
                    if now >= next_attempt or self._retry_event.is_set():
                        self._retry_event.clear()
                        connection = self._connect()
                        next_attempt = time.monotonic() + 2
                    else:
                        self._stop_event.wait(0.1)
                    continue

                try:
                    try:
                        command = self._commands.get(timeout=0.05)
                        self._write(connection, command)
                    except Empty:
                        pass

                    response = connection.readline().decode(errors="ignore").strip()
                    if response:
                        self._log("RX", response)
                except (serial.SerialException, OSError):
                    connection.close()
                    connection = None
                    self._set_status(False, f"Disconnected: {self.port}")
        finally:
            self._set_status(False, f"Disconnected: {self.port}")
            if connection is not None:
                connection.close()
