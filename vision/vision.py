import cv2
import time
import numpy as np
import fen


BOARD_SIZE = 800
SQUARES = 8
SQUARE_SIZE = BOARD_SIZE // SQUARES
files = "abcdefgh"


# -------------------------
# Utils
# -------------------------
def get_center(corner):
    return corner[0].mean(axis=0)


def pixel_to_square(x, y):
    col = int(x // SQUARE_SIZE)
    row = int(y // SQUARE_SIZE)

    if 0 <= row < 8 and 0 <= col < 8:
        return row, col
    return None


def mouse(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        print(x, y)


def create_detector():
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    params = cv2.aruco.DetectorParameters()
    return cv2.aruco.ArucoDetector(aruco_dict, params)


def draw_grid(img):
    for i in range(9):
        p = i * SQUARE_SIZE
        cv2.line(img, (p, 0), (p, BOARD_SIZE), (255, 255, 255), 1)
        cv2.line(img, (0, p), (BOARD_SIZE, p), (255, 255, 255), 1)


def replace_side(fen_string, side):
    fields = fen_string.split(" ")
    fields[1] = side
    return " ".join(fields)


def drain_serial(ser):
    while ser.in_waiting:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print(line)


# -------------------------
# Main
# -------------------------
def run_camera(ser):
    detector = create_detector()

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1600)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 900)

    cv2.namedWindow("cam")
    cv2.setMouseCallback("cam", mouse)

    last_time = time.time()

    # last 5 board measurements & whether its changed
    last_boards = []
    last_board = None
    next_side = "w"

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        corners, ids, _ = detector.detectMarkers(frame)

        # -------------------------
        # Build homography
        # -------------------------
        H = None
        marker_map = {}

        if ids is not None:
            for i, mid in enumerate(ids.flatten()):
                marker_map[int(mid)] = corners[i]

        if all(k in marker_map for k in [0, 1, 2, 3]):

            tl = get_center(marker_map[0])
            tr = get_center(marker_map[1])
            br = get_center(marker_map[2])
            bl = get_center(marker_map[3])

            src = np.array([tl, tr, br, bl], dtype=np.float32)

            dst = np.array([
                [0, 0],
                [BOARD_SIZE, 0],
                [BOARD_SIZE, BOARD_SIZE],
                [0, BOARD_SIZE]
            ], dtype=np.float32)

            H, _ = cv2.findHomography(src, dst)

        # -------------------------
        # Warp FIRST (only if possible)
        # -------------------------
        warped = np.zeros((BOARD_SIZE, BOARD_SIZE, 3), dtype=np.uint8)

        if H is not None:
            warped = cv2.warpPerspective(frame, H, (BOARD_SIZE, BOARD_SIZE))

        # -------------------------
        # Detect AGAIN in warped space
        # THIS is the key fix
        # -------------------------
        pieces = {}

        if H is not None:
            wc, wid, _ = detector.detectMarkers(warped)

            if wid is not None:
                for i, mid in enumerate(wid.flatten()):
                    c = wc[i]
                    center = get_center(c)
                    x, y = center

                    square = pixel_to_square(x, y)
                    if square is not None:
                        pieces[int(mid)] = square

        # -------------------------
        # Draw debug
        # -------------------------
        debug = warped.copy()
        draw_grid(debug)

        for mid, (row, col) in pieces.items():
            cv2.putText(
                debug,
                str(mid),
                (col * SQUARE_SIZE + 30, row * SQUARE_SIZE + 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        board = fen.build_board(pieces)
        fen_string = fen.board_to_fen(board)
        last_boards.append(fen_string)
        last_boards = last_boards[-5:]

        if len(last_boards) == 5 and all(b == last_boards[0] for b in last_boards):
            stabilized_board = last_boards[0]

            if last_board != stabilized_board:
                fen_to_send = replace_side(stabilized_board, next_side)
                ser.write(f"FEN {fen_to_send}\n".encode())
                ser.flush()
                drain_serial(ser)
                print("Board changed:", fen_to_send)
                last_board = stabilized_board
                next_side = "b" if next_side == "w" else "w"
        # -------------------------
        # FPS
        # -------------------------
        now = time.time()
        fps = 1 / (now - last_time)
        last_time = now

        cv2.putText(debug, f"{fps:.1f} FPS", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # -------------------------
        # Show
        # -------------------------
        cv2.imshow("cam", frame)
        cv2.imshow("board", warped)
        cv2.imshow("debug", debug)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()