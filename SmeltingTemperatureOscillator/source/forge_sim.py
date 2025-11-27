"""forge_sim.py

Configurable Chaotic Forge Temperature Simulator (with Bellows Surges)

Creates a wildly sporadic but bounded temperature curve using a
mean-reverting random walk (Ornstein-Uhlenbeck style), rare random spikes,
and bellows-triggered exponentially-decaying surges.

Dependencies: standard library + numpy + matplotlib

Author: generated per user prompt
"""

from __future__ import annotations

import argparse
import csv
import sys
from typing import List, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt


def simulate_forge(
    t_min: float,
    t_max: float,
    duration: float,
    sample_rate: float,
    reversion: float,
    volatility: float,
    spike_prob: float,
    spike_std: float,
    bellows_times: Optional[List[float]],
    surge_height: float,
    surge_half_life: float,
    seed: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Simulate forge temperature time series.

    Returns (t, temps) where t is seconds and temps is °C, both length N.

    The model is:
        T[i] = T[i-1] + theta*(T_mid - T[i-1])*dt + sigma*Normal(0, sqrt(dt))
                 + bellows_boost(i) + spike_jumps(i)

    Behavior:
    - Hard-clips the temperature to [t_min, t_max] at every step.
    - Rare gaussian spikes occur with probability `spike_prob` per step.
    - Each bellows time adds an exponentially decaying boost:
          boost(t) = surge_height * 0.5 ** ((t - t_press) / surge_half_life)
      for t >= t_press.
    """

    # Basic validation
    if t_max <= t_min:
        raise ValueError("t_max must be greater than t_min")
    if duration <= 0:
        raise ValueError("duration must be positive")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if surge_half_life <= 0:
        raise ValueError("surge_half_life must be positive")

    # allow seed == -1 to mean 'use non-deterministic entropy' (not reproducible)
    if seed == -1:
        rng = np.random.default_rng()
    else:
        rng = np.random.default_rng(seed)

    dt = 1.0 / float(sample_rate)
    n_steps = int(np.ceil(duration * sample_rate)) + 1
    t = np.linspace(0.0, duration, n_steps)

    # default spike_std if not provided (caller usually sets it)
    if spike_std is None:
        spike_std = (t_max - t_min) * 0.10

    # Prepare bellows times: filter out-of-range and optionally generate
    if bellows_times is None or len(bellows_times) == 0:
        # choose N in [4,6]
        N = int(rng.integers(4, 7))
        if duration <= 8:
            # too short to space with margin; place N presses uniformly across duration
            base = np.linspace(0.5 * duration / (N + 1), duration - 0.5 * duration / (N + 1), N)
            bellows_times = base.tolist()
        else:
            base = np.linspace(4, max(4.1, duration - 4), N)
            # jitter slightly to avoid strict periodicity
            spacing = base[1] - base[0] if len(base) > 1 else max(0.5, duration / (N + 1))
            jitter = rng.uniform(-0.25 * spacing, 0.25 * spacing, size=N)
            bellows_times = (base + jitter).tolist()
    else:
        # convert to floats and filter
        bellows_times = [float(x) for x in bellows_times]

    # Warn if any bellows out of range, and clip to valid list
    valid_bellows = []
    for bt in bellows_times:
        if 0.0 <= bt <= duration:
            valid_bellows.append(bt)
        else:
            print(f"Warning: bellows time {bt} outside [0, {duration}] and will be ignored", file=sys.stderr)
    bellows_times = sorted(valid_bellows)

    # Precompute T_mid and arrays
    T_mid = 0.5 * (t_min + t_max)
    temps = np.empty_like(t)
    temps[0] = float(np.clip(T_mid, t_min, t_max))

    # For each time step, compute bellows boost quickly by summing contributions
    # We'll compute per-step to keep the noise/spike logic straightforward.
    for i in range(1, len(t)):
        T_prev = temps[i - 1]
        # mean-reversion drift
        drift = reversion * (T_mid - T_prev) * dt
        # stochastic noise scaled appropriately
        noise = volatility * rng.normal(0.0, np.sqrt(dt))

        # rare spike
        spike = 0.0
        if rng.random() < spike_prob:
            spike = rng.normal(0.0, spike_std)

        # bellows boosts: sum of contributions from each press that has occurred
        # Using exponential 0.5 ** ((t - t_press)/half_life)
        bellows_boost = 0.0
        ti = t[i]
        # Iterate bellows (list typically small)
        for bt in bellows_times:
            if ti >= bt:
                # (ti - bt) / surge_half_life might be large, but 0.5**large decays
                bellows_boost += surge_height * (0.5 ** ((ti - bt) / surge_half_life))

        T_new = T_prev + drift + noise + bellows_boost + spike
        # Hard clip to bounds
        if T_new < t_min:
            T_new = t_min
        elif T_new > t_max:
            T_new = t_max

        temps[i] = T_new

    return t, temps


def _parse_bellows_list(values: Optional[List[str]]) -> Optional[List[float]]:
    if values is None:
        return None
    try:
        return [float(v) for v in values]
    except Exception:
        raise argparse.ArgumentTypeError("Bellows times must be numbers")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Chaotic Forge Temperature Simulator with Bellows Surges")
    parser.add_argument("--t-min", type=float, default=950.0, help="minimum temperature (°C)")
    parser.add_argument("--t-max", type=float, default=1250.0, help="maximum temperature (°C)")
    parser.add_argument("--duration", type=float, default=60.0, help="total seconds to simulate")
    parser.add_argument("--sample-rate", type=float, default=20.0, help="samples per second")
    parser.add_argument("--reversion", type=float, default=0.35, help="mean-reversion speed θ")
    parser.add_argument("--volatility", type=float, default=10.0, help="noise scale σ")
    parser.add_argument("--spike-prob", type=float, default=0.008, help="probability of a spike per time step")
    parser.add_argument("--spike-std", type=float, default=None, help="std dev for random spikes (default 10% of range)")
    parser.add_argument("--surge-height", type=float, default=95.0, help="bellows surge peak Δ°C")
    parser.add_argument("--surge-half-life", type=float, default=1.0, help="exponential half-life in seconds")
    parser.add_argument("--bellows-times", type=float, nargs="*", help="optional bellows press times in seconds; if omitted, generated automatically")
    parser.add_argument("--seed", type=int, default=22, help="RNG seed for reproducibility (set -1 for non-deterministic runs)")
    parser.add_argument("--out-png", type=str, default="forge_sim.png", help="path for saved plot PNG")
    parser.add_argument("--out-csv", type=str, default=None, help="optional path to write CSV file with time_s,temp_c")
    parser.add_argument("--no-plot", action="store_true", help="skip showing the interactive plot; file will still be saved")

    args = parser.parse_args(argv)

    # Validate
    if args.t_max <= args.t_min:
        parser.error("--t-max must be greater than --t-min")
    if args.duration <= 0:
        parser.error("--duration must be positive")
    if args.sample_rate <= 0:
        parser.error("--sample-rate must be positive")
    if args.surge_half_life <= 0:
        parser.error("--surge-half-life must be positive")

    # set default spike_std if omitted
    spike_std = args.spike_std if args.spike_std is not None else (args.t_max - args.t_min) * 0.10

    # bellows times list or None
    bellows_times = args.bellows_times if args.bellows_times is not None and len(args.bellows_times) > 0 else None

    print("Simulating forge with parameters:")
    print(f"  t_min={args.t_min}, t_max={args.t_max}, duration={args.duration}s, sample_rate={args.sample_rate}Hz")
    print(f"  reversion={args.reversion}, volatility={args.volatility}, spike_prob={args.spike_prob}, spike_std={spike_std}")
    print(f"  surge_height={args.surge_height}, surge_half_life={args.surge_half_life}, seed={args.seed}")

    t, temps = simulate_forge(
        t_min=args.t_min,
        t_max=args.t_max,
        duration=args.duration,
        sample_rate=args.sample_rate,
        reversion=args.reversion,
        volatility=args.volatility,
        spike_prob=args.spike_prob,
        spike_std=spike_std,
        bellows_times=bellows_times,
        surge_height=args.surge_height,
        surge_half_life=args.surge_half_life,
        seed=args.seed,
    )

    # Plot
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(t, temps, lw=1.2, color="#cc3e2b")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Chaotic Forge Temperature Simulation")
    ax.grid(alpha=0.25)

    # Mean reversion level (midpoint) - draw a red dashed line
    T_mid_plot = 0.5 * (args.t_min + args.t_max)
    ax.axhline(T_mid_plot, color="red", linestyle="--", alpha=0.9, label=f"Mean ({T_mid_plot:.0f}°C)")

    # draw bellows vertical lines if any (note: simulate_forge filters invalid ones)
    # we reconstruct bellows times by detecting significant local boosts: easier is to accept input again
    bellows_to_mark = []
    if args.bellows_times is None or len(args.bellows_times) == 0:
        # We cannot reconstruct generated bellows times here; instead call simulate for generation
        # Re-run with same seed to retrieve generated bellows times (cheap)
        _, _ = simulate_forge(
            t_min=args.t_min,
            t_max=args.t_max,
            duration=args.duration,
            sample_rate=args.sample_rate,
            reversion=args.reversion,
            volatility=args.volatility,
            spike_prob=args.spike_prob,
            spike_std=spike_std,
            bellows_times=None,
            surge_height=args.surge_height,
            surge_half_life=args.surge_half_life,
            seed=args.seed,
        )
        # Because the function prints warnings and generated times, we instruct the user to provide times
        # However, to mark on the plot we can try to detect times where temp rises sharply; simple heuristic:
        dt = 1.0 / args.sample_rate
        deriv = np.diff(temps) / dt
        # mark points where derivative exceeds mean + 2*std
        thr = np.mean(deriv) + 2.0 * np.std(deriv)
        spike_idx = np.where(deriv > thr)[0]
        cand_times = t[spike_idx + 1]
        # keep up to 10 unique candidates spaced by at least surge_half_life/2
        if cand_times.size > 0:
            filtered = [cand_times[0]]
            for ct in cand_times[1:]:
                if ct - filtered[-1] > 0.5 * args.surge_half_life:
                    filtered.append(ct)
            bellows_to_mark = filtered[:10]
    else:
        # use provided bellows times filtered to interval
        bellows_to_mark = [bt for bt in args.bellows_times if 0.0 <= bt <= args.duration]

    for bt in bellows_to_mark:
        ax.axvline(bt, color="#2b7cc8", linestyle="--", alpha=0.8)

    # show legend (includes mean line)
    ax.legend(loc="upper right")

    # horizontal clamps for t_min/t_max
    ax.axhline(args.t_min, color="gray", linestyle=":", alpha=0.8)
    ax.axhline(args.t_max, color="gray", linestyle=":", alpha=0.8)

    plt.tight_layout()
    plt.savefig(args.out_png, dpi=200)
    print(f"Saved plot to {args.out_png}")

    if not args.no_plot:
        try:
            plt.show()
        except Exception:
            # In headless environments, plt.show may fail; continue silently
            pass

    # Optionally write CSV
    if args.out_csv:
        try:
            with open(args.out_csv, "w", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(["time_s", "temp_c"])
                for ti, temp in zip(t, temps):
                    writer.writerow([f"{ti:.6f}", f"{temp:.6f}"])
            print(f"Saved CSV to {args.out_csv}")
        except Exception as exc:
            print(f"Failed to write CSV: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


"""
Example usage:

python forge_sim.py --t-min 950 --t-max 1250 --duration 60 --sample-rate 20 \
  --reversion 0.35 --volatility 10.0 --spike-prob 0.008 --spike-std 30 \
  --surge-height 95 --surge-half-life 1.0 --bellows-times 8 15 28 38 52 \
  --seed 42 --out-png advanced_forge.png --out-csv advanced_forge.csv

The script provides a small API function `simulate_forge(...)` which can be imported
and used programmatically. It keeps dependencies minimal (numpy + matplotlib).
"""
