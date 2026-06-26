TAG_TO_PIECE = {
    4: ("rook", "w"),
    5: ("knight", "w"),
    6: ("bishop", "w"),
    7: ("queen", "w"),
    8: ("king", "w"),
    9: ("bishop", "w"),
    10: ("knight", "w"),
    11: ("rook", "w"),

    12: ("pawn", "w"),
    13: ("pawn", "w"),
    14: ("pawn", "w"),
    15: ("pawn", "w"),
    16: ("pawn", "w"),
    17: ("pawn", "w"),
    18: ("pawn", "w"),
    19: ("pawn", "w"),
    20: ("pawn", "w"),
    21: ("pawn", "w"),
    22: ("pawn", "w"),
    23: ("pawn", "w"),

    24: ("pawn", "b"),
    25: ("pawn", "b"),
    26: ("pawn", "b"),
    27: ("pawn", "b"),
    28: ("pawn", "b"),
    29: ("pawn", "b"),
    30: ("pawn", "b"),
    31: ("pawn", "b"),

    32: ("rook", "b"),
    33: ("knight", "b"),
    34: ("bishop", "b"),
    35: ("queen", "b"),
    36: ("king", "b"),
    37: ("bishop", "b"),
    38: ("knight", "b"),
    39: ("rook", "b"),
}

PIECE_TO_FEN = {
    ("pawn", "w"): "P",
    ("knight", "w"): "N",
    ("bishop", "w"): "B",
    ("rook", "w"): "R",
    ("queen", "w"): "Q",
    ("king", "w"): "K",

    ("pawn", "b"): "p",
    ("knight", "b"): "n",
    ("bishop", "b"): "b",
    ("rook", "b"): "r",
    ("queen", "b"): "q",
    ("king", "b"): "k",
}

def build_board(pieces):
    board = [[None for _ in range(8)] for _ in range(8)]

    for tag, (row, col) in pieces.items():
        board[row][col] = tag

    return board

def board_to_fen(board):
    fen_rows = []

    for row in range(8):
        empty = 0
        fen_row = ""

        for col in range(8):
            cell = board[row][col]

            if cell is None:
                empty += 1
            else:
                if empty > 0:
                    fen_row += str(empty)
                    empty = 0

                piece = TAG_TO_PIECE.get(cell)

                if piece is None:
                    fen_char = "?"
                else:
                    fen_char = PIECE_TO_FEN[piece]

                fen_row += fen_char

        if empty > 0:
            fen_row += str(empty)
        
        fen_rows.append(fen_row)

    return "/".join(fen_rows) + " w - - 0 1"