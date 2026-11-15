"""SX-8 field simulator — original synthesized score.
A minor, 120 BPM, event-synced hits, ~20 s (video time = source time / 1.5).
"""
import numpy as np, wave, sys

SR = 48000
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(20261115)
t_all = np.arange(N) / SR

L = np.zeros(N); R = np.zeros(N)

def add(sig, at, gain=1.0, pan=0.0):
    """mix a mono signal into the stereo bus at time `at` (seconds)"""
    i0 = int(at * SR)
    if i0 >= N or i0 < 0:
        return
    n = min(len(sig), N - i0)
    wl = np.sqrt(0.5 * (1 - pan)); wr = np.sqrt(0.5 * (1 + pan))
    L[i0:i0+n] += sig[:n] * gain * wl
    R[i0:i0+n] += sig[:n] * gain * wr

def env(n, a=0.0, d=0.15, curve=4.0):
    x = np.arange(n) / SR
    e = np.exp(-x * curve / max(d, 1e-4))
    if a > 0:
        na = max(1, int(a * SR))
        e[:min(na, n)] *= np.linspace(0, 1, min(na, n))
    return e

def sine(f, dur, amp=1.0, phase=0.0):
    n = int(dur * SR); x = np.arange(n) / SR
    return amp * np.sin(2 * np.pi * f * x + phase)

def noise(dur, amp=1.0):
    n = int(dur * SR)
    return amp * rng.normal(0, 1, n)

def lowpass(sig, cutoff, order=2):
    """simple one-pole cascade"""
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = sig.copy()
    for _ in range(order):
        out = np.zeros_like(y); acc = 0.0
        for i in range(len(y)):
            acc = a * acc + (1 - a) * y[i]
            out[i] = acc
        y = out
    return y

def highpass(sig, cutoff, order=2):
    return sig - lowpass(sig, cutoff, order)

def bandpass(sig, lo, hi):
    return highpass(lowpass(sig, hi, 2), lo, 2)

# ---------------------------------------------------------------- instruments
def kick():
    d = 0.42
    n = int(d * SR); x = np.arange(n) / SR
    f = 92 * np.exp(-x * 26) + 44
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-x * 9.5)
    click = highpass(noise(0.02, 1.0), 2500) * env(int(0.02 * SR), d=0.02, curve=3)
    out = np.zeros(n); out[:len(body)] += body * 0.95
    out[:len(click)] += click * 0.35
    return out

def hat():
    n = int(0.075 * SR)
    s = highpass(noise(0.075, 1.0), 6000, 2)
    return s * env(n, d=0.075, curve=6) * 0.42

def pluck(f, dur=0.32, amp=1.0):
    n = int(dur * SR); x = np.arange(n) / SR
    s = (np.sin(2*np.pi*f*x) + 0.42*np.sin(2*np.pi*2*f*x + 0.8) * np.exp(-x*22)
         + 0.18*np.sin(2*np.pi*3*f*x + 1.6) * np.exp(-x*30))
    return s * env(n, d=dur, curve=3.2) * amp

def pad(f, dur, amp=1.0):
    n = int(dur * SR); x = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2*np.pi*0.3*x)
    s = (np.sin(2*np.pi*f*vib*x) * 0.6 + np.sin(2*np.pi*f*1.5*x + 0.4) * 0.22
         + np.sin(2*np.pi*f*2.02*x + 1.1) * 0.10)
    e = np.minimum(1.0, x / 0.45) * np.minimum(1.0, (dur - x) / 0.5)
    return s * e * amp

def thud(amp=1.0):
    n = int(0.55 * SR); x = np.arange(n) / SR
    s = np.sin(2*np.pi*(58*np.exp(-x*7) + 34)*x) * np.exp(-x*7)
    rattle = bandpass(noise(0.55, 1.0), 180, 1400) * np.exp(-x*16) * 0.5
    return (s + rattle) * amp

def servo(dur, f0, f1, amp=1.0, am=38):
    n = int(dur * SR); x = np.arange(n) / SR
    f = f0 + (f1 - f0) * (x / dur)
    ph = 2*np.pi*np.cumsum(f)/SR
    s = np.sin(ph) + 0.30*np.sin(2*ph + 0.5)
    s *= (0.55 + 0.45*np.sin(2*np.pi*am*x)) * np.minimum(1, np.minimum(x/0.05, (dur-x)/0.05))
    return s * amp

def clack(f=2200, amp=1.0):
    n = int(0.11 * SR)
    s = bandpass(noise(0.11, 1.0), f*0.7, f*1.5) * env(n, d=0.11, curve=7)
    ring = np.sin(2*np.pi*f*np.arange(n)/SR) * env(n, d=0.11, curve=9) * 0.35
    return (s + ring) * amp

def hiss(dur, amp=1.0):
    n = int(dur * SR)
    s = highpass(noise(dur, 1.0), 1800, 2) * (0.25 + 0.75*np.minimum(1, np.minimum(np.arange(n)/SR/0.06, (dur-np.arange(n)/SR)/0.12)))
    return s * amp

def whoosh(dur=0.9, amp=1.0):
    n = int(dur * SR); x = np.arange(n)/SR
    s = bandpass(noise(dur, 1.0), 300, 2600)
    e = np.sin(np.pi * (x / dur) ** 0.8) ** 2
    return s * e * amp

def chime(f, dur=0.9, amp=1.0):
    n = int(dur*SR); x = np.arange(n)/SR
    s = np.sin(2*np.pi*f*x) * env(n, d=dur, curve=4.5)
    return s * amp

# ---------------------------------------------------------------- music bed
BEAT = 0.5
def b(t): return t / BEAT

CHORDS = {  # (root, [partials])
  'Am': (110.0, [1, 1.5, 2.5, 3.0]),
  'F':  (87.3,  [1, 1.55, 2.4, 3.1]),
  'C':  (130.8, [1, 1.5, 2.0, 2.7]),
  'G':  (98.0,  [1, 1.5, 2.5, 3.2]),
  'Dm': (146.8, [1, 1.5, 2.5, 3.0]),
  'E':  (82.4,  [1, 1.5, 2.0, 2.9]),
}
PROG = [(0.0,'Am'),(2.0,'F'),(4.0,'C'),(6.0,'G'),(8.0,'Dm'),(10.0,'Am'),(12.0,'E'),(14.0,'Am'),(16.0,'E'),(18.0,'Am')]

for i,(tt,ch) in enumerate(PROG):
    dur = 2.0
    root, parts = CHORDS[ch]
    for k,mult in enumerate(parts):
        add(pad(root*mult, dur*1.06, 0.30/(k+1)), tt, gain=0.55, pan=(-0.25 if k%2==0 else 0.25))
    # sub
    add(sine(root*0.5, dur, 0.55) * np.minimum(1, np.arange(int(dur*SR))/SR/0.25), tt, gain=0.42, pan=0.0)

# kick + hat groove
beat_t = 2.0
while beat_t < 19.2:
    add(kick(), beat_t, gain=0.62, pan=0.0)
    beat_t += BEAT
hat_t = 2.25
while hat_t < 19.0:
    add(hat(), hat_t, gain=0.30, pan=0.18)
    hat_t += BEAT * 0.5

# arpeggio 16ths
arp_t = 6.0
step = 0.125
idx = 0
while arp_t < 18.6:
    ch = None
    for tt,ch2 in PROG:
        if arp_t >= tt: ch = ch2
    root, parts = CHORDS[ch or 'Am']
    f = root * ([1, 1.5, 2.0, 2.5][idx % 4])
    if idx % 8 in (3, 6):
        f *= 1.5
    add(pluck(f, 0.28, 0.55), arp_t, gain=0.22, pan=(-0.3 if idx%2 else 0.3))
    arp_t += step; idx += 1

# ---------------------------------------------------------------- event hits
# rappel: silk servo whirr
add(servo(1.55, 520, 340, 0.55, am=26), 0.02, gain=0.30, pan=-0.1)
add(servo(1.5, 360, 610, 0.30, am=44), 1.4, gain=0.12, pan=0.2)

# touchdown impact
add(thud(1.0), 1.54, gain=0.75)
add(clack(1500, 0.6), 1.56, gain=0.30, pan=0.1)
add(clack(2100, 0.5), 1.63, gain=0.22, pan=-0.1)

# walk ticks (source 3.6-7.6 -> 2.4-5.07, gait 0.44 s)
wt = 2.55
while wt < 5.0:
    add(clack(2600, 0.35), wt, gain=0.16, pan=0.12 if int(wt*4)%2 else -0.12)
    wt += 0.22

# leap: crouch, launch, land
add(servo(0.55, 300, 700, 0.5, am=30), 5.05, gain=0.22, pan=0.0)
add(whoosh(1.05, 0.9), 5.45, gain=0.30, pan=0.1)
add(thud(0.85), 6.44, gain=0.55)
add(clack(1200, 0.7), 6.47, gain=0.26)

# optics: three telescoping clicks
for k in range(3):
    add(clack(3000 + k*260, 0.55), 6.95 + k*0.33, gain=0.24, pan=0.16)
add(servo(0.9, 700, 1150, 0.32, am=60), 6.9, gain=0.16, pan=0.0)
add(chime(880, 0.85, 0.5), 7.85, gain=0.12)

# carapace: six hinge clacks
for k in range(6):
    add(clack(1800 + (k%3)*420, 0.6), 8.55 + k*0.17, gain=0.19, pan=(-0.25 if k%2 else 0.25))
add(servo(0.8, 420, 620, 0.35, am=34), 8.5, gain=0.14)

# leg L2: pneumatic hiss + lock
add(hiss(0.85, 0.9), 9.9, gain=0.24, pan=-0.2)
add(clack(900, 0.8), 10.72, gain=0.30, pan=-0.16)
add(thud(0.6), 10.75, gain=0.22)

# abdomen: spool whirr + petals
add(servo(0.95, 900, 1500, 0.30, am=72), 11.5, gain=0.16, pan=0.15)
add(clack(1600, 0.65), 12.55, gain=0.22, pan=0.1)

# fangs: two snips + sampler servo
add(servo(0.7, 640, 980, 0.3, am=48), 13.15, gain=0.15, pan=0.0)
add(clack(3400, 0.7), 13.42, gain=0.26, pan=0.08)
add(clack(3400, 0.7), 13.84, gain=0.26, pan=-0.08)
add(chime(1320, 0.7, 0.4), 14.05, gain=0.10)

# teardown: stutter hits + clatter bed
for k,tt in enumerate([14.35, 15.05, 15.65, 16.25]):
    add(thud(0.55 + 0.05*k), tt, gain=0.32)
    add(clack(1900 + 300*k, 0.5), tt + 0.02, gain=0.22, pan=(-0.2 if k%2 else 0.2))
add(hiss(2.3, 0.55), 14.4, gain=0.14, pan=0.0)

# reassembly: rising lock cascade
for k in range(4):
    add(clack(1400 + 200*k, 0.55), 17.05 + k*0.32, gain=0.22, pan=(-0.2 if k%2 else 0.2))
add(servo(1.2, 380, 820, 0.35, am=40), 17.0, gain=0.16)

# ascend: rising whirr + final resolve hit
add(servo(1.5, 420, 1300, 0.5, am=52), 18.45, gain=0.30, pan=0.0)
add(chime(660, 1.1, 0.7), 19.35, gain=0.22)
add(thud(0.5), 19.45, gain=0.30)

# ---------------------------------------------------------------- master
mix = np.stack([L, R])
# gentle high shelf roll-off + soft clip
mix = np.tanh(mix * 1.05) * 0.92
# fade in / out
nfi, nfo = int(0.12*SR), int(0.35*SR)
mix[:, :nfi] *= np.linspace(0, 1, nfi)
mix[:, -nfo:] *= np.linspace(1, 0, nfo)

peak = np.max(np.abs(mix))
mix = mix / max(peak, 1e-9) * 0.89

out = (mix.T * 32767).astype(np.int16)
path = sys.argv[1] if len(sys.argv) > 1 else "media/score.wav"
with wave.open(path, "wb") as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes(out.tobytes())
print("wrote", path, out.shape)
