from pathlib import Path
import pandas as pd

exp_dir = Path.home() / "alpasim" / "autolab_experiments"
records = []

for r in sorted(exp_dir.glob("run_*")):
    pqs = list(r.glob("**/metrics*.parquet"))
    vids = list(r.glob("**/*.mp4"))
    if not pqs or not vids:
        continue
    try:
        df = pd.read_parquet(pqs[0])
        vid_path = next((v for v in vids if "front_wide_120fov" in v.name), vids[0])
        records.append({
            "run_name": r.name,
            "collision": bool(df.get("collision_at_fault", [False])[0]),
            "open_loop": float(df.get("open_loop_collision", [0.0])[0]),
            "dist_traveled": float(df.get("dist_traveled_m", [0.0])[0]),
            "plan_dev": float(df.get("plan_deviation", [0.0])[0]),
            "video": str(vid_path.resolve())
        })
    except Exception:
        continue

df = pd.DataFrame(records)
crashes = df[df["collision"] == True]
safes = df[df["collision"] == False]

if len(crashes) == 0:
    print("[!] No crash records found.")
    exit(0)

early_crash = crashes.sort_values("dist_traveled").iloc[0]
late_crash = crashes.sort_values("dist_traveled", ascending=False).iloc[0]
safe_run = safes.sort_values("plan_dev").iloc[0] if len(safes) > 0 else None

print("=== 1. IMMEDIATE HANDOVER COLLAPSE ===")
print(f"Run: {early_crash['run_name']} | Distance: {early_crash['dist_traveled']:.1f}m | OpenLoop: {early_crash['open_loop']}")
print(f"Path: {early_crash['video']}\n")

print("=== 2. MID-DRIVE PLANNING COLLAPSE ===")
print(f"Run: {late_crash['run_name']} | Distance: {late_crash['dist_traveled']:.1f}m | OpenLoop: {late_crash['open_loop']}")
print(f"Path: {late_crash['video']}\n")

if safe_run is not None:
    print("=== 3. SAFE BASELINE ===")
    print(f"Run: {safe_run['run_name']} | Distance: {safe_run['dist_traveled']:.1f}m | PlanDev: {safe_run['plan_dev']:.2f}m")
    print(f"Path: {safe_run['video']}")
