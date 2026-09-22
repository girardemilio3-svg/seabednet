#!/usr/bin/env python3
"""One-shot: where does producer time go? Times corpus.sample under the exact
training mix (min_valid=0.9, 30% want-10m) and reports acceptance rates."""
import time, numpy as np
from v5_data import Corpus

corpus = Corpus(P=256)
rng = np.random.default_rng(0)

for label, want_res in (("100m", 100.0), ("10m", 10.0)):
    t0 = time.time(); ok = 0; none_ = 0
    for _ in range(60):
        s = corpus.sample(min_valid=0.9, want_res=want_res)
        if s is None: none_ += 1
        else: ok += 1
    dt = time.time() - t0
    print(f"{label}: {ok} ok / {none_} None in {dt:.1f}s -> {dt/60*1000:.0f} ms/call", flush=True)

# full training-mix batch of 16, like _produce_proc
t0 = time.time()
n = 0
while n < 16:
    want10 = rng.random() < 0.3 and corpus.n10 > 20
    s = corpus.sample(min_valid=0.9, want_res=10.0 if want10 else 100.0)
    if s is None:
        s = corpus.sample(min_valid=0.9)
    if s is None: continue
    n += 1
print(f"one batch of 16: {time.time()-t0:.1f}s  (x6 workers => batch every {(time.time()-t0)/6:.1f}s)", flush=True)
print("BENCH_DONE")
