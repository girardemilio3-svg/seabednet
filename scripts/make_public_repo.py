#!/usr/bin/env python3
"""Assemble the public SeabedNet repository from the working directory: code, results, sealed claims and proofs,
documentation. Sanitises as it copies (absolute home paths, contact details, anything naming a third party), and
refuses to ship a file that still matches the secret patterns. Large inputs, model weights and raster outputs stay
out; the README says where they live.  -> ../seabednet-public/
usage: python3 make_public_repo.py [--out DIR]"""
import os, re, shutil, sys, glob, json, subprocess, datetime

OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.expanduser("~/seabednet-public")
SRC = os.environ.get("SEABEDNET_WORKDIR", os.path.dirname(os.path.abspath(__file__)))   # the working directory this repo is assembled from
KEEP = {".git", "README.md", "LICENSE", "CITATION.cff", ".gitignore"}   # curated by hand; a rebuild must not eat them
if os.path.isdir(OUT):
    for _e in os.listdir(OUT):
        if _e in KEEP: continue
        _p = os.path.join(OUT, _e); shutil.rmtree(_p) if os.path.isdir(_p) else os.remove(_p)
else: os.makedirs(OUT)

# ---------------------------------------------------------------- what ships
CODE = {
 "src/model": ["v5_model.py", "v5_data.py", "v5_train.py", "train_hazard.py"],
 "src/inference": ["national_v5.py", "ensemble_v6.py", "blend_map.py", "hazard_corridor.py", "seabednet_complete.py", "corridor_complete.py", "national_complete.py"],
 "src/eval": ["temporal_eval.py", "ensemble_temporal.py", "hybrid_eval.py", "indep_validate.py", "baselines.py", "gebco_eval.py", "sigma_calibrate.py", "stratified_eval.py", "csb_eval.py", "csb_eval2.py", "candidates_vs_csb.py", "is2_v2.py", "is2_fetch_controls.py", "is2_claims.py", "is2_analyze.py", "icesat2_eval.py", "navwarn_hindcast.py", "hindcast.py", "hindcast_blind.py", "grade_forecast.py", "ckpt_eval.py"],
 "src/data": ["fetch.py", "fetch_many.py", "fetch10.py", "national_fetch.py", "make_gravity_prior.py", "make_tiles.py", "make_tiles10.py", "aux_build.py", "s1_build.py", "navwarn_archive.py", "chart_age.py", "index_coverage.py", "profile_catzoc.py", "make_benchmark.py", "bench_sampler.py", "patch_builders.py"],
 "src/products": ["shoal_list.py", "shoal_list_v2.py", "danger_model.py", "danger_model2.py", "danger_apply.py", "national_plan.py", "national_plan_v2.py", "survey_planner.py", "make_forecast.py", "prospective_forecast.py", "prospective_score.py", "community_cards.py", "predict_strikes.py", "find_corridor.py", "shoal_labels.py"],
 "src/site": ["build_atlas_v9.py", "build_atlas_v8.py", "build_atlas_v7.py", "build_atlas_v6.py", "build_atlas_v5.py", "build_atlas_v2.py", "build_report.py", "canada_v5_render.py", "corridor_render.py", "national_render.py"],
}
EXTRA_CODE = [("src/data/csb_crawl.py", "recon_csb/csb_crawl.py")]
SCRIPTS = {   # historical pipeline chains, renamed to what they actually do
 "scripts/pipeline/01_channels_and_full_models.sh": "chain_spark7.sh",
 "scripts/pipeline/02_hazard_from_scratch.sh": "chain_spark5.sh",
 "scripts/pipeline/03_seed_ensemble.sh": "chain_spark8.sh",
 "scripts/pipeline/04_augmented_inference_and_v6_map.sh": "chain_spark9.sh",
 "scripts/pipeline/05_distance_blend.sh": "chain_spark10.sh",
 "scripts/pipeline/06_test_time_augmentation_evals.sh": "chain_tta_eval.sh",
 "scripts/publish_atlas.sh": "publish_v8.sh",
}
DOCS = {"docs/METHODS.md": "PAPER.md", "docs/RUNNING_THE_MODEL.md": "PACKAGE.md", "docs/SURVEY_PLAN.md": "SURVEY_PLAN.md",
        "docs/RESEARCH_STATEMENT.md": "RESEARCH_STATEMENT.md", "docs/VALIDATION_REPORT.md": "validation_report.md", "docs/PLAN_v2.md": "PLAN_v2.md"}
# every result JSON is small and is the evidence behind the atlas; sealed lists and their timestamp proofs ship too
RESULT_JSON = sorted(glob.glob(os.path.join(SRC, "*.json")))
SEALED = ["shoal_list_v2_2026-09-06.csv", "shoal_list_2026-09-03.csv", "forecast_2026-09-02.csv", "strike_predictions_2026-09-03.csv", "forecast_top_positions.csv"]
PROOFS = sorted(glob.glob(os.path.join(SRC, "*.ots")))
NAVWARN = ["recon_navwarn/danger_points.csv", "recon_navwarn/cancelled_danger_points.csv"]
# never ship: private strategy, third-party contacts, other projects, rentals, raw data, weights, rasters
NEVER = re.compile(r"(OUTREACH|PRESS_BRIEF|pitchkit|TARGETS|chain_3090|after_3090|run_|resume_|film_|render_film|frames|\.pt$|\.npz$|\.npy$|tiles|_out/|cache)")

SCRIPT_PY = {}
for _folder, _files in CODE.items():
    for _f in _files: SCRIPT_PY[_f] = _folder.split("/", 1)[1]
SCRIPT_PY["csb_crawl.py"] = "data"
HEADER = """#!/bin/sh
# {TITLE} — one of the chains that produced the published models, kept as it ran.
# It expects the data layout in docs/METHODS.md (NONNA tiles, channels and weights in the working directory)
# and writes its outputs there. Run from anywhere: paths resolve against the repository root.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
"""

# ---------------------------------------------------------------- sanitising
HOME = os.path.expanduser("~")
SUBS = [
 (re.compile(re.escape(HOME) + r"/seabednet/?"), ""),                      # absolute project paths -> repo-relative
 (re.compile(re.escape(HOME)), "$HOME"),
 (re.compile(r"girardemilio3@gmail\.com"), "see the repository profile"),  # contact details out of the code
 (re.compile(r"\b\d{3}-\d{3}-\d{4}\b"), "[redacted]"),
]
FORBIDDEN = re.compile(r"ghp_|github_pat_|gh auth token|BEGIN [A-Z ]*PRIVATE KEY|api[_-]?key\s*=\s*['\"][^'\"]{8,}|password\s*=\s*['\"]|vast\.ai|\b100\.112\.\d+\.\d+\b|@gmail\.com|\b\d{3}-\d{3}-\d{4}\b", re.I)

def sanitise(text):
    for pat, rep in SUBS: text = pat.sub(rep, text)
    return text

def put(rel, src_path, text_mode=True):
    dst = os.path.join(OUT, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not text_mode: shutil.copy(src_path, dst); return
    t = sanitise(open(src_path, encoding="utf-8", errors="replace").read())
    open(dst, "w", encoding="utf-8").write(t)

def write(rel, text):
    if os.path.basename(rel) == "README.md" and os.path.exists(os.path.join(OUT, rel)): return
    dst = os.path.join(OUT, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(text)

n = 0
for folder, files in CODE.items():
    for f in files:
        p = os.path.join(SRC, f)
        if os.path.exists(p) and not NEVER.search(f): put(f"{folder}/{f}", p); n += 1
for rel, f in EXTRA_CODE:
    p = os.path.join(SRC, f)
    if os.path.exists(p): put(rel, p); n += 1
for rel, f in SCRIPTS.items():
    p = os.path.join(SRC, f)
    if os.path.exists(p):
        t = sanitise(open(p, encoding="utf-8").read())
        t = re.sub(r"^cd\s*;", "cd \"$ROOT\";", t, flags=re.M)          # the sanitiser removes the absolute path
        t = re.sub(r"^cd\s*$", 'cd "$ROOT"', t, flags=re.M)
        for name, sub in SCRIPT_PY.items(): t = t.replace(f"python3 {name}", f'python3 "$ROOT/src/{sub}/{name}"')
        t = re.sub(r"chain_spark(\d+)\.log", lambda m: f"pipeline_{m.group(1)}.log", t)
        head = HEADER.replace("{TITLE}", os.path.basename(rel))
        t = re.sub(r"^#!/bin/sh\n", head, t, count=1)
        write(rel, t); os.chmod(os.path.join(OUT, rel), 0o755); n += 1
for rel, f in DOCS.items():
    p = os.path.join(SRC, f)
    if os.path.exists(p): put(rel, p); n += 1
for p in RESULT_JSON:
    b = os.path.basename(p)
    if NEVER.search(b) or os.path.getsize(p) > 3_000_000: continue
    put(f"results/{b}", p); n += 1
for f in SEALED + NAVWARN:
    p = os.path.join(SRC, f)
    if os.path.exists(p) and os.path.getsize(p) < 5_000_000: put(f"results/sealed/{os.path.basename(f)}" if f in SEALED else f"results/navwarn/{os.path.basename(f)}", p); n += 1
for p in PROOFS:
    put(f"results/sealed/{os.path.basename(p)}", p, text_mode=False); n += 1
if os.path.isdir(os.path.join(SRC, "benchmark")):
    shutil.copytree(os.path.join(SRC, "benchmark"), os.path.join(OUT, "benchmark")); n += len(glob.glob(os.path.join(OUT, "benchmark/**/*"), recursive=True))

# ---------------------------------------------------------------- audit
bad = []
for p in glob.glob(os.path.join(OUT, "**/*"), recursive=True):
    if not os.path.isfile(p) or os.path.splitext(p)[1] in (".ots", ".npz", ".png", ".jpg"): continue
    try: t = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    for m in FORBIDDEN.finditer(t): bad.append((os.path.relpath(p, OUT), m.group(0)[:40]))
print("files:", n, "| audit hits:", len(bad))
for r in bad[:20]: print("   !", r)
json.dump({"built": datetime.date.today().isoformat(), "files": n, "audit_hits": len(bad)}, open(os.path.join(OUT, "results/repo_build.json"), "w"), indent=1)
