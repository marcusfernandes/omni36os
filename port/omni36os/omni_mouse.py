"""Omni36OS — modo mouse e teclado virtuais (uinput), dentro do serviço de atalhos.

Modo mouse (FN + R3 ou o menu de energia; arquivo /dev/shm/omni36os-mouse = "1"):
  analógico direito move o cursor, analógico esquerdo rola a página,
  A ou R3 = clique, B = clique direito. O resto do controle continua indo para o programa.
  Enquanto ele está ligado, o controle fica agarrado (EVIOCGRAB) pelo serviço de atalhos e o que
  não é do mouse é devolvido (o mesmo "vai e volta" do FnGate).

Teclado: o menu de energia abre o teclado do Omni36OS por cima do programa; o texto fica em
/dev/shm/omni36os-power/digitar e é digitado aqui assim que o programa volta.

Kernel 4.4: o uinput é criado do jeito antigo (write de uinput_user_dev + UI_DEV_CREATE).
"""
import fcntl
import os
import struct
import time

FLAG = "/dev/shm/omni36os-mouse"
TYPE_FILE = "/dev/shm/omni36os-power/digitar"
EV_SYN, EV_KEY, EV_REL, EV_ABS = 0, 1, 2, 3
REL_X, REL_Y, REL_WHEEL, REL_HWHEEL = 0, 1, 8, 6
BTN_LEFT, BTN_RIGHT = 0x110, 0x111
UI_SET_EVBIT, UI_SET_KEYBIT, UI_SET_RELBIT = 0x40045564, 0x40045565, 0x40045566
UI_DEV_CREATE = 0x5501
EVENT = struct.Struct("llHHi")

PAD_A, PAD_B, PAD_R3 = 305, 304, 707
AX_LX, AX_LY, AX_RX, AX_RY = 0, 1, 3, 4
RANGE, DEAD = 1800, 220
SPEED = 16.0                      # px por quadro (60/s) com o analógico no fim
CLICKS = {PAD_A: BTN_LEFT, PAD_R3: BTN_LEFT, PAD_B: BTN_RIGHT}

# texto -> (tecla, shift) no layout US (o WebKit e o SDL recebem o caractere certo)
_KEYS = {}
for i, ch in enumerate("1234567890"):
    _KEYS[ch] = (2 + i, False)
for row, start in (("qwertyuiop", 16), ("asdfghjkl", 30), ("zxcvbnm", 44)):
    for i, ch in enumerate(row):
        _KEYS[ch] = (start + i, False)
        _KEYS[ch.upper()] = (start + i, True)
for ch, code, sh in ((" ", 57, False), ("\n", 28, False), ("-", 12, False), ("_", 12, True), ("=", 13, False),
                     ("+", 13, True), ("[", 26, False), ("]", 27, False), (";", 39, False), (":", 39, True),
                     ("'", 40, False), ('"', 40, True), (",", 51, False), ("<", 51, True), (".", 52, False),
                     (">", 52, True), ("/", 53, False), ("?", 53, True), ("\\", 43, False), ("|", 43, True),
                     ("!", 2, True), ("@", 3, True), ("#", 4, True), ("$", 5, True), ("%", 6, True),
                     ("^", 7, True), ("&", 8, True), ("*", 9, True), ("(", 10, True), (")", 11, True),
                     ("`", 41, False), ("~", 41, True), ("{", 26, True), ("}", 27, True)):
    _KEYS[ch] = (code, sh)
SHIFT = 42
_PLAIN = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ",
                       "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC")


def mode_on():
    try:
        with open(FLAG) as f:
            return f.read().strip() == "1"
    except OSError:
        return False


def set_mode(on):
    try:
        with open(FLAG, "w") as f:
            f.write("1" if on else "0")
        os.chmod(FLAG, 0o666)
    except OSError:
        pass


class Virtual:
    """Mouse + teclado virtuais (um dispositivo só)."""

    def __init__(self):
        self.fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
        for ev in (EV_KEY, EV_REL, EV_SYN):
            fcntl.ioctl(self.fd, UI_SET_EVBIT, ev)
        for rel in (REL_X, REL_Y, REL_WHEEL, REL_HWHEEL):
            fcntl.ioctl(self.fd, UI_SET_RELBIT, rel)
        for k in list(range(1, 120)) + [BTN_LEFT, BTN_RIGHT, 0x112]:
            fcntl.ioctl(self.fd, UI_SET_KEYBIT, k)
        name = b"Omni36OS mouse e teclado".ljust(80, b"\0")
        dev = name + struct.pack("HHHHi", 0x06, 0x1234, 0x5678, 1, 0) + b"\0" * (64 * 4 * 4)
        os.write(self.fd, dev)
        fcntl.ioctl(self.fd, UI_DEV_CREATE)

    def emit(self, events):
        os.write(self.fd, b"".join(EVENT.pack(0, 0, t, c, v) for t, c, v in events + [(EV_SYN, 0, 0)]))

    def type_text(self, text):
        for ch in text.translate(_PLAIN):
            k = _KEYS.get(ch)
            if not k:
                continue
            code, sh = k
            if sh:
                self.emit([(EV_KEY, SHIFT, 1)])
            self.emit([(EV_KEY, code, 1)])
            self.emit([(EV_KEY, code, 0)])
            if sh:
                self.emit([(EV_KEY, SHIFT, 0)])
            time.sleep(0.008)


def _speed(v):
    a = abs(v)
    if a <= DEAD:
        return 0.0
    f = min(1.0, (a - DEAD) / (RANGE - DEAD))
    return (f * f) * SPEED * (1 if v > 0 else -1)


class Mouse:
    """Liga o modo mouse em cima do FnGate do serviço de atalhos (mesmo fd do controle)."""

    def __init__(self):
        self.dev = None
        self.on = False
        self.axes = {AX_LX: 0, AX_LY: 0, AX_RX: 0, AX_RY: 0}
        self.acc = [0.0, 0.0, 0.0]
        self.checked = 0.0

    def _dev(self):
        if self.dev is None:
            self.dev = Virtual()
        return self.dev

    def poll(self, gate):
        """Confere o arquivo do modo (2x/s) e agarra ou solta o controle."""
        now = time.monotonic()
        if now - self.checked < 0.5:
            return
        self.checked = now
        want = mode_on()
        if want != self.on:
            self.on = want
            if want:
                self._dev()
                gate.grab(True)
            else:
                gate.release([])
                self.axes = dict.fromkeys(self.axes, 0)
        elif want and not gate.on:
            gate.grab(True)            # algo soltou (controle reaberto): agarra de novo
        if os.path.exists(TYPE_FILE):
            try:
                with open(TYPE_FILE) as f:
                    text = f.read()
                os.remove(TYPE_FILE)
                time.sleep(0.6)        # o programa acabou de descongelar
                self._dev().type_text(text)
            except OSError:
                pass

    def filter(self, gate, events):
        """Com o modo ligado: tira os eventos do mouse e devolve o resto ao programa."""
        out, back = [], []
        for ev in events:
            typ, code, val = ev
            if typ == EV_SYN:
                continue
            if gate.echo and ev == gate.echo[0]:
                gate.echo.pop(0)
                continue
            out.append(ev)                         # os atalhos com FN continuam vendo tudo
            if typ == EV_ABS and code in self.axes:
                self.axes[code] = val
            elif typ == EV_KEY and code in CLICKS and val != 2:
                self._dev().emit([(EV_KEY, CLICKS[code], val)])
            else:
                back.append(ev)
        if back:
            gate.inject(back)
        return out

    def tick(self):
        """Move o cursor e rola (chamado a ~60/s com o modo ligado)."""
        if not self.on:
            return
        self.acc[0] += _speed(self.axes[AX_RX])
        self.acc[1] += _speed(self.axes[AX_RY])
        self.acc[2] += -_speed(self.axes[AX_LY]) / 40
        evs = []
        for i, rel in ((0, REL_X), (1, REL_Y), (2, REL_WHEEL)):
            n = int(self.acc[i])
            if n:
                self.acc[i] -= n
                evs.append((EV_REL, rel, n))
        if evs:
            self._dev().emit(evs)
