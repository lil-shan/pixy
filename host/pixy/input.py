"""Control deck input for Pixy.

The STM32 scans the deck at 1 kHz and packs everything into one int32. This
module unpacks it into something a game loop can read, and is polled once per
frame rather than event-driven -- games ask "what is held right now" anyway,
and polling means a tap between frames still survives, because the MCU latches
presses until they are read.

    deck = Deck()
    while True:
        s = deck.poll()
        if s.pressed(A):  fire()
        paddle += s.enc(0)
"""

import time

UP, DOWN, LEFT, RIGHT, A, B, START, SELECT = range(8)

NAMES = {
    UP: "UP", DOWN: "DOWN", LEFT: "LEFT", RIGHT: "RIGHT",
    A: "A", B: "B", START: "START", SELECT: "SELECT",
}


def _s8(v):
    """Reinterpret the low byte as signed -- encoder deltas go both ways."""
    v &= 0xFF
    return v - 256 if v & 0x80 else v


class State:
    """One frame of input."""

    __slots__ = ("held", "_pressed", "_enc")

    def __init__(self, packed=0):
        self.held = packed & 0xFF
        self._pressed = (packed >> 8) & 0xFF
        self._enc = (_s8(packed >> 16), _s8(packed >> 24))

    def down(self, btn):
        """True for as long as the button is held. Use for movement."""
        return bool(self.held & (1 << btn))

    def pressed(self, btn):
        """True only on the frame the button went down. Use for actions."""
        return bool(self._pressed & (1 << btn))

    def enc(self, which=0):
        """Detents turned since the last poll. Positive is clockwise."""
        return self._enc[which]

    def any_pressed(self):
        return self._pressed != 0

    def __repr__(self):
        names = [n for b, n in NAMES.items() if self.down(b)]
        return f"<State held={names or '-'} enc={self._enc}>"


class BridgeDeck:
    """Real hardware, over the App Lab router bridge."""

    def __init__(self):
        # Imported lazily: this only resolves inside the App Lab container,
        # and we want the mock backend to work everywhere else.
        from arduino.app_utils import call

        @call(timeout=2)
        def poll_input() -> int:
            ...

        @call("beep", timeout=1)
        def _beep(freq: int, ms: int):
            ...

        self._poll = poll_input
        self._beep = _beep

    def poll(self):
        try:
            return State(self._poll())
        except Exception:
            # A dropped frame of input must never take the console down.
            return State(0)

    def beep(self, freq=880, ms=40):
        try:
            self._beep(int(freq), int(ms))
        except Exception:
            pass


class KeyboardDeck:
    """Stand-in so games can be built before the deck is wired.

    Arrow keys move, Z is A, X is B, Enter is Start, Tab is Select, and
    , / . turn encoder 1 while [ / ] turn encoder 2.
    """

    KEYMAP = {
        "\x1b[A": UP, "\x1b[B": DOWN, "\x1b[D": LEFT, "\x1b[C": RIGHT,
        "z": A, "x": B, "\r": START, "\t": SELECT,
    }
    ENCMAP = {",": (0, -1), ".": (0, +1), "[": (1, -1), "]": (1, +1)}

    def __init__(self):
        import sys, termios, tty
        self._sys, self._termios, self._tty = sys, termios, tty
        self._fd = sys.stdin.fileno()
        self._saved = termios.tcgetattr(self._fd)
        tty.setcbreak(self._fd)
        self._held = 0
        self._release_at = {}

    def poll(self):
        import select
        pressed, enc = 0, [0, 0]
        while select.select([self._sys.stdin], [], [], 0)[0]:
            ch = self._sys.stdin.read(1)
            if ch == "\x1b":                       # escape sequence, read the rest
                ch += self._sys.stdin.read(2)
            if ch in self.ENCMAP:
                which, delta = self.ENCMAP[ch]
                enc[which] += delta
            elif ch in self.KEYMAP:
                b = self.KEYMAP[ch]
                pressed |= 1 << b
                self._held |= 1 << b
                # A keyboard has no key-up here, so synthesise a short hold.
                self._release_at[b] = time.time() + 0.12

        now = time.time()
        for b, t in list(self._release_at.items()):
            if now >= t:
                self._held &= ~(1 << b)
                del self._release_at[b]

        packed = (self._held & 0xFF) | ((pressed & 0xFF) << 8)
        packed |= (enc[0] & 0xFF) << 16
        packed |= (enc[1] & 0xFF) << 24
        return State(packed)

    def beep(self, freq=880, ms=40):
        pass

    def close(self):
        self._termios.tcsetattr(self._fd, self._termios.TCSADRAIN, self._saved)


def Deck(force=None):
    """Real deck when the bridge is there, keyboard when it isn't."""
    if force == "keyboard":
        return KeyboardDeck()
    try:
        return BridgeDeck()
    except Exception as e:
        print(f"[pixy] bridge unavailable ({e}); using keyboard input")
        return KeyboardDeck()
