import unittest

from protocol import ProtocolState


BOARD_FEN = "8/8/8/8/8/8/8/8 w - - 0 1"


class ProtocolStateTests(unittest.TestCase):
    def test_first_automatic_send_uses_white_and_advances_side(self):
        state = ProtocolState()

        self.assertEqual(state.automatic_command(BOARD_FEN), "FEN 8/8/8/8/8/8/8/8 w - - 0 1")
        state.mark_sent(BOARD_FEN)

        self.assertEqual(state.next_side, "b")
        self.assertIsNone(state.automatic_command(BOARD_FEN))

    def test_pause_defers_board_until_resumed(self):
        state = ProtocolState()
        state.set_auto_send_enabled(False)

        self.assertIsNone(state.automatic_command(BOARD_FEN))

        state.set_auto_send_enabled(True)
        self.assertEqual(state.automatic_command(BOARD_FEN), "FEN 8/8/8/8/8/8/8/8 w - - 0 1")

    def test_manual_send_advances_following_automatic_side(self):
        state = ProtocolState()

        self.assertEqual(state.manual_command(BOARD_FEN), "FEN 8/8/8/8/8/8/8/8 w - - 0 1")
        state.mark_sent(BOARD_FEN)

        next_board = "8/8/8/8/8/8/8/7K w - - 0 1"
        self.assertEqual(state.automatic_command(next_board), "FEN 8/8/8/8/8/8/8/7K b - - 0 1")


if __name__ == "__main__":
    unittest.main()
