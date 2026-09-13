"""Render text and images for a 64x32 HUB75 panel and ship them to the XIAO.

All the interesting work happens here, on the UNO Q's Linux side: real fonts,
image scaling, GIF decoding, scrolling. The XIAO downstream only copies
finished RGB565 frames onto the panel.

    from panel import Panel
    p = Panel()
    p.text("HELLO")
    p.image("logo.png")
    p.scroll("longer message here")
"""

import glob
import socket
import struct
import time
from PIL import Image, ImageDraw, ImageFont, ImageSequence

WIDTH, HEIGHT = 64, 32

MAGIC = b"\xA5\x5A"
CMD_FRAME = 0x01
CMD_BRIGHTNESS = 0x02
CMD_CLEAR = 0x03
CMD_PING = 0x04
ACK = 0x06

# Bundled bitmap fonts are unreadable below ~8px, so a real TTF matters here.
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]


def _autodetect_port():
    """Pick the XIAO's port, skipping the UNO Q's own USB gadget interface."""
    ports = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
    if not ports:
        raise RuntimeError("no serial ports found - is the XIAO plugged in?")
    return ports[-1]


def load_font(size=12, path=None):
    for candidate in ([path] if path else []) + FONT_CANDIDATES:
        if not candidate:
            continue
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def to_rgb565(img):
    """Pack a 64x32 RGB image into big-endian RGB565, matching the receiver."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    if img.size != (WIDTH, HEIGHT):
        img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    out = bytearray(WIDTH * HEIGHT * 2)
    i = 0
    for r, g, b in img.getdata():
        v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        out[i] = v >> 8
        out[i + 1] = v & 0xFF
        i += 2
    return bytes(out)


class Panel:
    def __init__(self, host=None, port=None, baud=921600, settle=2.0,
                 tcp_port=3333):
        """Connect over WiFi if `host` is given, otherwise over USB serial.

        The wire protocol is identical either way, so everything below this
        point is transport-agnostic.
        """
        if host:
            self.kind = "tcp"
            self.port = f"{host}:{tcp_port}"
            self.sock = socket.create_connection((host, tcp_port), timeout=5)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.settimeout(3.0)
            self.ser = None
        else:
            import serial
            self.kind = "serial"
            self.port = port or _autodetect_port()
            # On the ESP32-S3's USB Serial/JTAG peripheral, DTR and RTS drive
            # reset and boot-mode selection. pyserial asserts both on open by
            # default, which resets the chip or leaves it unable to receive.
            # Clear them before opening -- after is already too late.
            self.ser = serial.Serial()
            self.ser.port = self.port
            self.ser.baudrate = baud
            self.ser.timeout = 1
            self.ser.dtr = False
            self.ser.rts = False
            self.ser.open()
            self.ser.reset_input_buffer()
            self.sock = None
            time.sleep(settle)

    # -- wire ----------------------------------------------------------------

    def _write(self, data):
        if self.kind == "tcp":
            self.sock.sendall(data)
        else:
            self.ser.write(data)
            self.ser.flush()

    def _read1(self):
        try:
            return self.sock.recv(1) if self.kind == "tcp" else self.ser.read(1)
        except (socket.timeout, OSError):
            return b""

    def _send(self, cmd, payload=b"", wait_ack=False, timeout=2.0):
        self._write(MAGIC + struct.pack("<BH", cmd, len(payload)) + payload)
        if not wait_ack:
            return True
        deadline = time.time() + timeout
        while time.time() < deadline:
            b = self._read1()
            if b and b[0] == ACK:
                return True
        return False

    def ping(self, timeout=2.0):
        """Round-trip check: True if the receiver is listening and answering."""
        return self._send(CMD_PING, wait_ack=True, timeout=timeout)

    def show(self, img, wait_ack=False):
        """Push one PIL image to the panel."""
        return self._send(CMD_FRAME, to_rgb565(img), wait_ack=wait_ack)

    def brightness(self, value):
        self._send(CMD_BRIGHTNESS, bytes([max(0, min(255, int(value)))]))

    def clear(self):
        self._send(CMD_CLEAR)

    def close(self):
        (self.sock or self.ser).close()

    # -- drawing -------------------------------------------------------------

    def blank(self, colour=(0, 0, 0)):
        return Image.new("RGB", (WIDTH, HEIGHT), colour)

    def text(self, msg, colour=(255, 255, 255), bg=(0, 0, 0), size=12, font=None):
        """Draw a single line, centred. Shrinks the text until it fits."""
        img = self.blank(bg)
        draw = ImageDraw.Draw(img)
        for pt in range(size, 5, -1):
            f = load_font(pt, font)
            box = draw.textbbox((0, 0), msg, font=f)
            w, h = box[2] - box[0], box[3] - box[1]
            if w <= WIDTH:
                draw.text(((WIDTH - w) // 2 - box[0], (HEIGHT - h) // 2 - box[1]),
                          msg, font=f, fill=colour)
                break
        self.show(img)
        return img

    def scroll(self, msg, colour=(255, 255, 255), bg=(0, 0, 0),
               size=14, font=None, speed=0.03, loops=1):
        """Scroll a line right to left. Any length, any font."""
        f = load_font(size, font)
        probe = ImageDraw.Draw(self.blank())
        box = probe.textbbox((0, 0), msg, font=f)
        w, h = box[2] - box[0], box[3] - box[1]

        for _ in range(loops):
            for x in range(WIDTH, -w - 1, -1):
                img = self.blank(bg)
                ImageDraw.Draw(img).text((x - box[0], (HEIGHT - h) // 2 - box[1]),
                                         msg, font=f, fill=colour)
                self.show(img)
                time.sleep(speed)

    def image(self, path, fit="contain", bg=(0, 0, 0)):
        """Show a still image, scaled to the panel."""
        src = Image.open(path).convert("RGB")
        if fit == "stretch":
            self.show(src.resize((WIDTH, HEIGHT), Image.LANCZOS))
            return
        scaled = src.copy()
        scaled.thumbnail((WIDTH, HEIGHT), Image.LANCZOS)
        img = self.blank(bg)
        img.paste(scaled, ((WIDTH - scaled.width) // 2,
                           (HEIGHT - scaled.height) // 2))
        self.show(img)

    def gif(self, path, loops=1, bg=(0, 0, 0)):
        """Play an animated GIF, honouring its own frame timings."""
        src = Image.open(path)
        frames = []
        for frame in ImageSequence.Iterator(src):
            rgb = frame.convert("RGB")
            rgb.thumbnail((WIDTH, HEIGHT), Image.LANCZOS)
            canvas = self.blank(bg)
            canvas.paste(rgb, ((WIDTH - rgb.width) // 2,
                               (HEIGHT - rgb.height) // 2))
            frames.append((canvas, frame.info.get("duration", 100) / 1000.0))
        for _ in range(loops):
            for img, delay in frames:
                self.show(img)
                time.sleep(delay)
