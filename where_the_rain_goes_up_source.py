#!/usr/bin/env python3
"""
WHERE THE RAIN GOES UP - the Fable's Day made thing, Oct 11 2026.

Seed: the final minute of Takemitsu's Rain Tree Sketch II (track 107,
listening room session one). His ending: a ritardando from 237 to 58 BPM,
the register sinking to A0, and then - after the floor - an upward spray
of treble: B4, D#5, G#5, A5, C6, E6. The piece below begins at that floor
and follows the spray upward until it evaporates.

Form (about 3 minutes):
  I.   THE FLOOR (0:00-0:40)   - A0/A1 pedal, enormous and slow, decaying.
                                  Sparse deep drops, slowing (his ritardando,
                                  continued past where the record stopped).
  II.  THE SPRAY (0:35-1:50)   - the six spray pitches arrive as rain-drop
                                  bells, stochastic, density growing; each
                                  generation spawns children an octave up.
  III. EVAPORATION (1:45-3:00) - only the high lattice remains, thinning,
                                  rising, until the last drops leave the top
                                  of hearing. Endings rise.

All sound is additive/FM bell synthesis - no samples, no copies. The only
thing borrowed from Takemitsu is a door he left open.
"""
import numpy as np

SR = 44100
DUR = 185.0
N = int(SR * DUR)
rng = np.random.default_rng(20261011)  # the date is the seed

L = np.zeros(N)
R = np.zeros(N)

def midi_f(m): return 440.0 * 2 ** ((m - 69) / 12)

def bell(freq, dur, amp, inharm=0.0014, brightness=1.0):
    """A struck-water bell: a few inharmonic partials with exponential decay."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    partials = [1.0, 2.0, 2.92, 4.07, 5.4]
    gains    = [1.0, 0.42 * brightness, 0.22 * brightness, 0.09 * brightness, 0.045 * brightness]
    decays   = [1.0, 1.7, 2.6, 3.6, 4.8]
    for p, g, d in zip(partials, gains, decays):
        f = freq * p * (1 + inharm * p * p)
        if f > SR / 2 - 200: continue
        env = np.exp(-t * d * (2.2 + freq / 900))
        out += g * env * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    att = int(0.002 * SR)
    if att > 0 and n > att:
        out[:att] *= np.linspace(0, 1, att)
    return amp * out

def place(sig, t0, pan):
    i = int(t0 * SR)
    if i >= N: return
    seg = sig[: max(0, N - i)]
    j = i + len(seg)
    gl = np.cos(pan * np.pi / 2); gr = np.sin(pan * np.pi / 2)
    L[i:j] += seg * gl
    R[i:j] += seg * gr

# ---------------------------------------------------------------- I. THE FLOOR
# A0 pedal - huge, soft, breathing. Two strikes, the second quieter.
for t0, amp in [(0.0, 0.50), (14.0, 0.33), (30.0, 0.20)]:
    sig = bell(midi_f(21), 28.0, amp, brightness=0.35)   # A0
    place(sig, t0, 0.5)
    sig2 = bell(midi_f(33), 24.0, amp * 0.5, brightness=0.4)  # A1 shadow
    place(sig2, t0 + 0.07, 0.5)

# deep drops, ritardando continuing past the record's end: gaps grow 2.6 -> 7 s
t = 4.0
gap = 2.6
floor_pitches = [33, 36, 40, 31, 38]  # A1, C2, E2, G1, D2 - dark water
k = 0
while t < 42 and gap < 7.5:
    m = floor_pitches[k % len(floor_pitches)]
    place(bell(midi_f(m), 12.0, 0.16, brightness=0.5), t, 0.5 + rng.uniform(-0.1, 0.1))
    t += gap
    gap *= 1.17
    k += 1

# ------------------------------------------------------------- II. THE SPRAY
SPRAY = [71, 75, 80, 81, 84, 88]   # B4, D#5, G#5, A5, C6, E6 - his spray, verbatim
# Rain as weather, not genealogy: a density curve over time, with the
# pitch-center drifting upward beneath it. The spray's six pitch classes
# are the only notes the rain is allowed to be.
def density(t):               # drops per second
    if t < 38:  return 0.0
    if t < 75:  return 0.25 + 3.0 * (t - 38) / 37          # gathering
    if t < 112: return 3.25                                  # full rain
    if t < 150: return 3.25 * max(0.04, (150 - t) / 38)      # thinning
    return 0.0

def center(t):                # midi center drifts B4 -> ~E7 across the rain
    return 71 + (t - 38) * (26.0 / 112.0)

PCS = sorted({p % 12 for p in SPRAY})   # {0,3,4,8,9,11}
def quantize(m):
    m = int(round(m))
    best = min(range(m - 6, m + 7), key=lambda x: (abs(x - m), x) if x % 12 in PCS else (99, x))
    return best

all_events = []
t = 38.0
while t < 152:
    lam = density(t)
    if lam <= 0:
        t += 0.5; continue
    t += rng.exponential(1.0 / lam)
    m = quantize(rng.normal(center(t), 5.5))
    m = max(69, min(106, m))
    gen = max(0, int((m - 71) / 7))
    all_events.append((t, m, gen))
print(f"rain drops: {len(all_events)}")

for t0, m, gen in all_events:
    f = midi_f(m)
    amp = 0.13 * (0.85 ** gen) * rng.uniform(0.7, 1.0)
    dur = max(1.5, 7.0 - gen * 0.7)
    pan = np.clip(0.5 + rng.normal(0, 0.22), 0.05, 0.95)
    place(bell(f, dur, amp, brightness=1.1), t0, pan)

# ---------------------------------------------------------- III. EVAPORATION
# the lattice thins; the last drops are the highest. A slow glittering rain
# above C7 that spaces out logarithmically - the record player lifting its arm.
t = 148.0
gap = 0.9
top = [96, 100, 103, 105, 108]  # C7 upward - the spray's grandchildren
k = 0
while t < DUR - 6:
    m = top[k % len(top)] + int(rng.choice([0, 0, 12] if t > 165 else [0]))
    if m <= 110:
        amp = 0.07 * max(0.15, 1.0 - (t - 148) / 34)
        place(bell(midi_f(m), 5.0, amp, brightness=1.3), t, np.clip(0.5 + rng.normal(0, 0.3), 0.05, 0.95))
    t += gap
    gap *= 1.22
    k += 1

# one last A - the floor's ghost, four octaves up, barely there. the tree remembers.
place(bell(midi_f(93), 9.0, 0.055, brightness=0.8), DUR - 11.0, 0.5)  # A6

# ------------------------------------------------------------------ MASTER
mix = np.stack([L, R], axis=1)
# gentle highpass rumble control & soft clip guard
peak = np.max(np.abs(mix))
mix = mix / peak * 0.89
# a whisper of room: single comb reflection
d = int(0.031 * SR)
mix[d:] += 0.18 * mix[:-d][:, ::-1]
mix = mix / np.max(np.abs(mix)) * 0.91

from scipy.io import wavfile
wavfile.write("/home/claude/outputs/where_the_rain_goes_up.wav", SR, (mix * 32767).astype(np.int16))
print(f"rendered {DUR:.0f}s, {len(all_events)} spray drops, peak-normalized")
