from dataclasses import dataclass
import threading
import time

import cv2
import numpy as np

import fen


BOARD_SIZE = 800
SQUARES = 8
SQUARE_SIZE = BOARD_SIZE // SQUARES


@dataclass(frozen=True)
class CameraSnapshot:
    frame: np.ndarray | None
    pieces: dict[int, tuple[int, int]]
    stable_fen: str | None
    fps: float
    status: str


def get_center(corner):
    return corner[0].mean(axis=0)


def pixel_to_square(x, y):
    col = int(x // SQUARE_SIZE)
    row = int(y // SQUARE_SIZE)

    if 0 <= row < SQUARES and 0 <= col < SQUARES:
        return row, col
    return None


def create_detector():
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    params = cv2.aruco.DetectorParameters()
    return cv2.aruco.ArucoDetector(aruco_dict, params)


def replace_side(fen_string, side):
    fields = fen_string.split(" ")
    fields[1] = side
    return " ".join(fields)


class CameraWorker:
    """Continuously capture and detect board state without touching the UI."""

    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._snapshot = CameraSnapshot(None, {}, None, 0.0, "Starting camera")

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1)

    def snapshot(self):
        with self._lock:
            return self._snapshot

    def _publish(self, frame, pieces, stable_fen, fps, status):
        with self._lock:
            self._snapshot = CameraSnapshot(
                frame=frame,
                pieces=dict(pieces),
                stable_fen=stable_fen,
                fps=fps,
                status=status,
            )

    def _open_camera(self):
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1600)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 900)
        return cap

    def _run(self):
        detector = create_detector()
        cap = None
        last_boards = []
        stable_fen = None
        last_time = time.monotonic()

        try:
            while not self._stop_event.is_set():
                if cap is None or not cap.isOpened():
                    if cap is not None:
                        cap.release()
                    cap = self._open_camera()
                    if not cap.isOpened():
                        self._publish(None, {}, stable_fen, 0.0, "Camera unavailable")
                        self._stop_event.wait(1)
                        continue

                ret, frame = cap.read()
                if not ret:
                    cap.release()
                    cap = None
                    self._publish(None, {}, stable_fen, 0.0, "Camera frame unavailable")
                    self._stop_event.wait(0.25)
                    continue

                corners, ids, _ = detector.detectMarkers(frame)
                annotated = frame.copy()
                marker_map = {}

                if ids is not None:
                    cv2.aruco.drawDetectedMarkers(annotated, corners, ids)
                    for index, marker_id in enumerate(ids.flatten()):
                        marker_map[int(marker_id)] = corners[index]

                homography = None
                if all(marker_id in marker_map for marker_id in (0, 1, 2, 3)):
                    source = np.array(
                        [
                            get_center(marker_map[0]),
                            get_center(marker_map[1]),
                            get_center(marker_map[2]),
                            get_center(marker_map[3]),
                        ],
                        dtype=np.float32,
                    )
                    destination = np.array(
                        [
                            [0, 0],
                            [BOARD_SIZE, 0],
                            [BOARD_SIZE, BOARD_SIZE],
                            [0, BOARD_SIZE],
                        ],
                        dtype=np.float32,
                    )
                    homography, _ = cv2.findHomography(source, destination)

                pieces = {}
                if homography is not None:
                    warped = cv2.warpPerspective(frame, homography, (BOARD_SIZE, BOARD_SIZE))
                    warped_corners, warped_ids, _ = detector.detectMarkers(warped)
                    if warped_ids is not None:
                        for index, marker_id in enumerate(warped_ids.flatten()):
                            if int(marker_id) not in fen.TAG_TO_PIECE:
                                continue
                            square = pixel_to_square(*get_center(warped_corners[index]))
                            if square is not None:
                                pieces[int(marker_id)] = square

                candidate_fen = fen.board_to_fen(fen.build_board(pieces))
                last_boards.append(candidate_fen)
                last_boards = last_boards[-5:]
                if len(last_boards) == 5 and len(set(last_boards)) == 1:
                    stable_fen = last_boards[0]

                now = time.monotonic()
                fps = 1 / max(now - last_time, 0.001)
                last_time = now
                cv2.putText(
                    annotated,
                    f"{fps:.1f} FPS",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
                self._publish(annotated, pieces, stable_fen, fps, "Camera connected")
        finally:
            if cap is not None:
                cap.release()
