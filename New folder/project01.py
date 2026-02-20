from scipy.optimize import minimize

# ============================================================
# Helpers
# ============================================================

def read_int_min(prompt, min_value=1):
    while True:
        try:
            v = int(input(prompt))
            if v >= min_value:
                return v
            print(f"Value must be at least {min_value}.")
        except ValueError:
            print("Please enter an integer number.")

def read_float_range(prompt, low, high):
    while True:
        try:
            v = float(input(prompt))
            if low <= v <= high:
                return v
            print(f"Value must be between {low} and {high}.")
        except ValueError:
            print("Please enter a numeric value.")

def compute_blend(x, sources_data):
    # sources_data[i][j] = percent passing of source i at sieve j
    m = len(sources_data[0])   # number of sieves
    n = len(sources_data)      # number of sources
    blend = []
    for j in range(m):
        total = 0.0
        for i in range(n):
            total += x[i] * sources_data[i][j]
        blend.append(total)
    return blend

def objective_midpoint_ls(x, sources_data, target_midpoints):
    blend = compute_blend(x, sources_data)
    total = 0.0
    for j in range(len(target_midpoints)):
        d = blend[j] - target_midpoints[j]
        total += d * d
    return total

# ============================================================
# Main
# ============================================================

# 1) number of sources
sources = read_int_min("Please enter the number of aggregate resources: ", 1)

# 2) sieves (must match your project statement)
sieves = (19, 12.5, 4, 10, 40, 80, 200)

# 3) read sources gradation data
sources_data = []
for i in range(sources):
    print(f"\n--- Source {i+1} ---")
    one_source = []
    for s in sieves:
        val = read_float_range(f"Enter the percentage passing the sieve {s}: ", 0, 100)
        one_source.append(val)
    sources_data.append(one_source)

# 4) read range (min/max) per sieve, then compute midpoint target
ideal_min = []
ideal_max = []

print("\n--- Enter RANGE for each sieve (MIN then MAX). Range is used ONLY to compute midpoint target. ---")
for s in sieves:
    vmin = read_float_range(f"sieve {s} MIN: ", 0, 100)
    vmax = read_float_range(f"sieve {s} MAX: ", 0, 100)
    if vmax < vmin:
        print("⚠️ MAX was smaller than MIN, swapping them.")
        vmin, vmax = vmax, vmin
    ideal_min.append(vmin)
    ideal_max.append(vmax)

target = [(lo + hi) / 2.0 for lo, hi in zip(ideal_min, ideal_max)]

# 5) optimization constraints
constraints = [{"type": "eq", "fun": lambda x: sum(x) - 1.0}]
bounds = [(0.0, 1.0)] * sources
x0 = [1.0 / sources] * sources

res = minimize(
    objective_midpoint_ls,
    x0,
    args=(sources_data, target),
    method="SLSQP",
    bounds=bounds,
    constraints=constraints
)

# 6) prepare solution
if not res.success:
    print("\n⚠️ Optimization warning:", res.message)

x_opt = list(res.x)

# remove tiny numeric noise + renormalize to exactly sum=1
x_opt = [0.0 if abs(v) < 1e-12 else v for v in x_opt]
sx = sum(x_opt)
if sx != 0:
    x_opt = [v / sx for v in x_opt]

blend_opt = compute_blend(x_opt, sources_data)

# 7) one-line output
print("\n=== RESULT ===")
mix_line = " | ".join([f"S{i+1}={x_opt[i]*100:.2f}%" for i in range(len(x_opt))])
print(mix_line)

# 8) table output
print("\n=== TABLE (Sieve / Min / Max / Target(mid) / Blend / InRange) ===")
header = f"{'Sieve':>7} | {'Min':>7} | {'Max':>7} | {'Target':>10} | {'Blend':>7} | {'InRange':>7}"
print(header)
print("-" * len(header))

in_range_count = 0
for s, lo, hi, tg, bv in zip(sieves, ideal_min, ideal_max, target, blend_opt):
    in_range = (lo <= bv <= hi)
    if in_range:
        in_range_count += 1
    print(f"{str(s):>7} | {lo:7.2f} | {hi:7.2f} | {tg:10.2f} | {bv:7.2f} | {('YES' if in_range else 'NO'):>7}")

print(f"\nRange check: {in_range_count}/{len(sieves)} sieves within range.")
print("===============================================")
