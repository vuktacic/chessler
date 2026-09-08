import tkinter as tk
from tkinter import ttk

import cv2

import fen
from protocol import ProtocolState, SerialWorker
from vision import CameraWorker


PIECE_GLYPHS = {
    ("pawn", "w"): "♙",
    ("knight", "w"): "♘",
    ("bishop", "w"): "♗",
    ("rook", "w"): "♖",
    ("queen", "w"): "♕",
    ("king", "w"): "♔",
    ("pawn", "b"): "♟",
    ("knight", "b"): "♞",
    ("bishop", "b"): "♝",
    ("rook", "b"): "♜",
    ("queen", "b"): "♛",
    ("king", "b"): "♚",
}


class VisionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chessler Vision")
        self.root.minsize(1120, 760)

        self.camera = CameraWorker()
        self.serial = SerialWorker()
        self.protocol = ProtocolState()
        self._photo = None
        self._last_board = None

        self._build_layout()
        self.camera.start()
        self.serial.start()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._refresh()

    def _build_layout(self):
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(0, weight=3)
        self.root.rowconfigure(1, weight=2)

        camera_frame = ttk.LabelFrame(self.root, text="Camera")
        camera_frame.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        camera_frame.rowconfigure(0, weight=1)
        camera_frame.columnconfigure(0, weight=1)
        self.camera_label = ttk.Label(camera_frame, anchor="center", text="Waiting for camera")
        self.camera_label.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        self.camera_status = ttk.Label(camera_frame, anchor="w")
        self.camera_status.grid(row=1, column=0, padx=6, pady=(0, 6), sticky="ew")

        board_frame = ttk.LabelFrame(self.root, text="Detected Board (camera orientation)")
        board_frame.grid(row=0, column=1, padx=(0, 8), pady=8, sticky="nsew")
        board_frame.columnconfigure(0, weight=1)
        board_frame.rowconfigure(0, weight=1)
        self.board = tk.Frame(board_frame, bg="#1f1f1f")
        self.board.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        self.board_cells = []
        for row in range(8):
            self.board.rowconfigure(row, weight=1)
            row_cells = []
            for column in range(8):
                self.board.columnconfigure(column, weight=1)
                color = "#f0d9b5" if (row + column) % 2 == 0 else "#b58863"
                cell = tk.Label(
                    self.board,
                    bg=color,
                    justify="center",
                    font=("DejaVu Sans", 18),
                    width=5,
                    height=3,
                )
                cell.grid(row=row, column=column, sticky="nsew")
                row_cells.append(cell)
            self.board_cells.append(row_cells)

        terminal_frame = ttk.LabelFrame(self.root, text="Serial Terminal")
        terminal_frame.grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="nsew")
        terminal_frame.columnconfigure(0, weight=1)
        terminal_frame.rowconfigure(0, weight=1)
        self.log = tk.Text(
            terminal_frame,
            height=12,
            bg="#121212",
            fg="#e8e8e8",
            insertbackground="#e8e8e8",
            state="disabled",
            wrap="word",
        )
        self.log.grid(row=0, column=0, columnspan=3, padx=6, pady=6, sticky="nsew")
        self.command_entry = ttk.Entry(terminal_frame)
        self.command_entry.grid(row=1, column=0, padx=(6, 4), pady=(0, 6), sticky="ew")
        self.command_entry.bind("<Return>", self.send_terminal_command)
        self.send_button = ttk.Button(terminal_frame, text="Send", command=self.send_terminal_command)
        self.send_button.grid(row=1, column=1, padx=4, pady=(0, 6))
        self.retry_button = ttk.Button(terminal_frame, text="Retry", command=self.serial.retry)
        self.retry_button.grid(row=1, column=2, padx=(4, 6), pady=(0, 6))

        controls = ttk.Frame(terminal_frame)
        controls.grid(row=2, column=0, columnspan=3, padx=6, pady=(0, 6), sticky="ew")
        self.connection_status = ttk.Label(controls, anchor="w")
        self.connection_status.pack(side="left", fill="x", expand=True)
        self.pause_button = ttk.Button(controls, text="Pause Auto-send", command=self.toggle_auto_send)
        self.pause_button.pack(side="right", padx=(4, 0))
        self.current_fen_button = ttk.Button(
            controls,
            text="Send Current FEN",
            command=self.send_current_fen,
        )
        self.current_fen_button.pack(side="right")

    def _refresh(self):
        snapshot = self.camera.snapshot()
        self.camera_status.config(text=f"{snapshot.status} · {snapshot.fps:.1f} FPS")
        self._update_camera(snapshot.frame)
        self._update_board(snapshot.pieces)
        self._send_automatic_fen(snapshot.stable_fen)
        self._update_serial_state(snapshot.stable_fen)
        self._append_logs()
        self.root.after(30, self._refresh)

    def _update_camera(self, frame):
        if frame is None:
            self.camera_label.config(image="", text="Waiting for camera")
            self._photo = None
            return

        height, width = frame.shape[:2]
        scale = min(720 / width, 460 / height, 1)
        display = cv2.resize(frame, (int(width * scale), int(height * scale)))
        success, encoded = cv2.imencode(".png", display)
        if not success:
            return
        self._photo = tk.PhotoImage(data=encoded.tobytes(), format="png")
        self.camera_label.config(image=self._photo, text="")

    def _update_board(self, pieces):
        if pieces == self._last_board:
            return
        self._last_board = dict(pieces)
        squares = {square: tag for tag, square in pieces.items()}
        for row in range(8):
            for column in range(8):
                tag = squares.get((row, column))
                if tag is None:
                    text = ""
                else:
                    glyph = PIECE_GLYPHS.get(fen.TAG_TO_PIECE.get(tag), "?")
                    text = f"{glyph}\n{tag}"
                self.board_cells[row][column].config(text=text)

    def _send_automatic_fen(self, board_fen):
        if board_fen is None or not self.serial.status()[0]:
            return
        command = self.protocol.automatic_command(board_fen)
        if command is not None and self.serial.send(command):
            self.protocol.mark_sent(board_fen)

    def _update_serial_state(self, board_fen):
        connected, status = self.serial.status()
        self.connection_status.config(text=status)
        state = "normal" if connected else "disabled"
        self.command_entry.config(state=state)
        self.send_button.config(state=state)
        self.current_fen_button.config(state="normal" if connected and board_fen else "disabled")

    def _append_logs(self):
        logs = self.serial.drain_logs()
        if not logs:
            return
        self.log.config(state="normal")
        for item in logs:
            self.log.insert("end", f"{item.direction} {item.payload}\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def toggle_auto_send(self):
        enabled = not self.protocol.auto_send_enabled
        self.protocol.set_auto_send_enabled(enabled)
        self.pause_button.config(text="Pause Auto-send" if enabled else "Resume Auto-send")

    def send_current_fen(self):
        board_fen = self.camera.snapshot().stable_fen
        if board_fen is None:
            return
        command = self.protocol.manual_command(board_fen)
        if self.serial.send(command):
            self.protocol.mark_sent(board_fen)

    def send_terminal_command(self, _event=None):
        command = self.command_entry.get()
        if self.serial.send(command):
            self.command_entry.delete(0, "end")
        return "break"

    def close(self):
        self.camera.stop()
        self.serial.stop()
        self.root.destroy()


def run_ui():
    root = tk.Tk()
    VisionApp(root)
    root.mainloop()
