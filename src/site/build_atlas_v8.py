#!/usr/bin/env python3
"""Atlas v7 -> v8. Exhibit N: the prospective test (the danger forecast sealed on 2026-09-12 before any outcome, its hash and
OpenTimestamps proof, the scoring rule, and — once notices exist — the score). Also appends to Exhibit M's temporal table the
test-time-augmentation row and the six-member ensemble row when their json files exist."""
import json, os, shutil
def sub1(s, old, new):
    assert s.count(old) == 1, f"count {s.count(old)}: {old[:60]}"; return s.replace(old, new)
tr = lambda cells, th=False: "<tr>" + "".join(f"<{'th' if th else 'td'}>{c}</{'th' if th else 'td'}>" for c in cells) + "</tr>"
def load(fn): return json.load(open(fn)) if os.path.exists(fn) else None
src = open("churchill_atlas_v7.html", encoding="utf-8").read()
F = load("forecast_danger_2026-09-12.json"); SC = load("prospective_score_2026-09-12.json"); FS = load("forecast_danger_south_2026-09-13.json"); SCS = load("prospective_score_2026-09-13.json")
# --- Exhibit M additions
extra = []
for k, label in (("temporal_ctlfull_tta4", "Full size control + 4-fold test-time augmentation"), ("temporal_s1full_tta", "Full size + winter radar + 8-fold augmentation"), ("temporal_v6", "Ensemble of three full-size models (v6 map)"), ("temporal_v6x6", "Six-member augmented ensemble (v6 map, seeds 1&ndash;3 added)"), ("hybrid_ens3tta", "Ensemble + nearest-sounding blend inside 1 km (fit on half the blocks, scored on the other half)")):
    v = load(f"temporal_validation_{k}.json")
    if not v: continue
    o = v["overall"]; bd = v.get("by_depth", [])
    extra.append(tr([label, f"{o['mae_model']:.2f}", f"{o['mae_nn']:.2f}", f"{o['mae_grav']:.2f}", f"{o['frac_within_1sigma']*100:.0f}%", f"{bd[0]['mae_model']:.2f}" if bd else "&mdash;", f"{bd[1]['mae_model']:.2f}" if len(bd) > 1 else "&mdash;", f"{o['bias']:+.1f}"]))
if extra:
    i = src.find("Full size, full corpus, from scratch: + winter radar"); j = src.find("</tbody>", i); src = src[:j] + "".join(extra) + src[j:]

# --- Exhibit M: from-scratch hazard heads (negative result)
H = {}
for tag in ("_v2", "_v5ctl", "_v5s1"):
    for suf in ("", "_archive"):
        v = load(f"navwarn_hindcast{tag}{suf}.json")
        if v: H[tag + suf] = v["summary"]
if all(k in H for k in ("_v2", "_v5ctl", "_v5s1", "_v2_archive", "_v5ctl_archive", "_v5s1_archive")):
    g = lambda k, sub: f"{H[k][sub]['ge90']/max(1, H[k][sub]['n'])*100:.0f}%"
    para = f'''
  <h3 style="font-size:19px;margin:22px 0 6px">Hazard heads trained from scratch</h3>
  <p class="lede" style="font-size:14.5px">One more attempt at the hazard field, with and without winter radar, trained from scratch for 3,000 steps on the same recipe instead of warm-started from the published head. Neither beats the published head on the Coast Guard notices. Share of chart-safe notices landing in the top decile of the field, live set then archive: published {g("_v2", "map_safe")} / {g("_v2_archive", "map_safe")}; from scratch {g("_v5ctl", "map_safe")} / {g("_v5ctl_archive", "map_safe")}; from scratch with radar {g("_v5s1", "map_safe")} / {g("_v5s1_archive", "map_safe")}. On the blind subset (no sounding within 300 m) the radar head is worse: {g("_v5s1", "map_safe_blind")} against {g("_v2", "map_safe_blind")} live. The hazard field has reached the ceiling of what the soundings support; the danger-report model above is where the operational signal is.</p>'''
    anchor_J = '<section>\n  <div class="eyebrow">Exhibit J &mdash; sealed claims</div>'
    i = src.index(anchor_J); j = src.rfind("</section>", 0, i); src = src[:j] + para + "\n" + src[j:]

# --- laser v2 (stronger null) appended to the laser paragraph in Exhibit L/M if present, else to Exhibit N
V2 = load("is2_v2.json")
if V2 and V2.get("controls"):
    P = sum(c["passes"] for c in V2["controls"]); n_cl = len([c for c in V2["claims"] if "passes" in c]); one = [c for c in V2["claims"] if c.get("passes_with_bottom", 0) >= 1]
    para = f'''
  <p class="lede" style="font-size:13.5px"><b>Laser altimetry, second pass.</b> NASA's official ICESat-2 bathymetry product returns no photons anywhere in these waters (its search mask excludes them), so the raw photon data over all 36 claims were re-analysed with an along-track detector that requires a continuous bottom over 60 m, a gap between the surface and the bottom, and a Poisson test against each pass's own deep-water noise, with the detector echo at 3&ndash;5 m discarded. On {P} passes over two deep-water control sites it found no bottom at all, so it does not invent shoals. Over the claims it found a bottom on {len(one)} of {n_cl} sites, on a single pass each, none confirmed by a second pass. The honest reading is unchanged: in ice-affected Arctic water the laser cannot see 3&ndash;7 m shoals often enough to confirm or refute them, and the claims stand or fall with the next survey release. File <a href="is2_v2.json">is2_v2.json</a>.</p>'''
    anchor = '<section>\n  <div class="eyebrow">Exhibit J &mdash; sealed claims</div>'
    i = src.index(anchor); j = src.rfind("</section>", 0, i); src = src[:j] + para + "\n" + src[j:]; shutil.copy("is2_v2.json", "pages_repo/is2_v2.json")
# --- Exhibit N
if F:
    ots = os.path.exists(F["file"] + ".ots")
    score_html = ""
    if SC and SC.get("n_messages_inside", 0) > 0:
        m = SC["n_messages_inside"]; h = SC["msg_top_decile_hits"]; ci = SC["msg_top_decile_ci95"]; h1 = SC["msg_top_percentile_hits"]
        score_html = f'''
  <h3 style="font-size:19px;margin:22px 0 6px">Score as of {SC["scored"]}</h3>
  <div class="tblwrap"><table><thead>{tr(["Notices after the seal inside the forecast", "in the top decile (chance 10%)", "95% interval", "in the top percentile (chance 1%)", "median percentile"], True)}</thead><tbody>{tr([str(m), f"{h} ({h/m*100:.0f}%)", f"{ci[0]*100:.0f}&ndash;{ci[1]*100:.0f}%", f"{h1} ({h1/m*100:.0f}%)", f"{SC['median_percentile']}"])}</tbody></table></div>
  <p class="lede" style="font-size:13.5px">A notice with several positions counts once, by its best-scored position. Notices outside the forecast area (the St. Lawrence, the Maritimes, the Pacific coast) do not count either way. File <a href="prospective_score_2026-09-12.json">prospective_score_2026-09-12.json</a>.</p>'''

    if SCS and SCS.get("n_messages_inside", 0) > 0:
        m = SCS["n_messages_inside"]; h = SCS["msg_top_decile_hits"]; ci = SCS["msg_top_decile_ci95"]; h1 = SCS["msg_top_percentile_hits"]
        score_html += f'''
  <h3 style="font-size:19px;margin:22px 0 6px">Southern file, score as of {SCS["scored"]}</h3>
  <div class="tblwrap"><table><thead>{tr(["Notices after the seal inside the forecast", "in the top decile (chance 10%)", "95% interval", "in the top percentile (chance 1%)", "median percentile"], True)}</thead><tbody>{tr([str(m), f"{h} ({h/m*100:.0f}%)", f"{ci[0]*100:.0f}&ndash;{ci[1]*100:.0f}%", f"{h1} ({h1/m*100:.0f}%)", f"{SCS['median_percentile']}"])}</tbody></table></div>
  <p class="lede" style="font-size:13.5px">Read this carefully before repeating it. Nine of the ten notices are one survey campaign in Chedabucto Bay, Nova Scotia, issued on 17 and 18 September, four days after the seal put that bay in the top 1% of the country. That is one event, not nine. And the bay is not new to the Coast Guard: it produced 132 danger notices between 2019 and 2025, all of which the model saw in training, so this is a hit on a recurring area, not the discovery of an unknown one. The tenth notice, in the St. Lawrence estuary, landed at the 47th percentile: a miss. Two independent events so far, one hit and one miss. The interval above treats notices as independent and therefore overstates the evidence; the test keeps accumulating. File <a href="prospective_score_2026-09-13.json">prospective_score_2026-09-13.json</a>.</p>'''
    N = f'''<section>
  <div class="eyebrow">Exhibit N &mdash; the prospective test</div>
  <h2>A forecast sealed before the outcome, scored by the Coast Guard's own notices</h2>
  <p class="lede">Every test so far is a hindcast: soundings we already had were hidden and recovered. This one is not. On {F["sealed"]} the danger-report model's score for every chart-safe cell in the Arctic and Hudson Bay corridors ({F["n_cells"]:,} cells over {F["n_blocks"]} blocks at 500 m spacing: chart-safe water within 30 km of a Natural Resources Canada shipping route or node, or 15 km of a community) was written to a file, hashed and timestamped. Nothing in it can be changed. Every Coast Guard danger notice issued after that date (shallow depth confirmed or reported, shoal, uncharted rock, submerged object) with a position inside the forecast area scores it, under a rule that was fixed at sealing time and written into the file's manifest.</p>
  <div class="tblwrap"><table><thead>{tr(["File", "Sealed", "Last notice id seen", "Cells", "SHA-256", "Proof"], True)}</thead><tbody>{tr(["Arctic and Hudson Bay corridors", F["sealed"], str(F["cutoff_id"]), f"{F['n_cells']:,}", f'<code style="font-size:11.5px">{F["sha256"]}</code>', ('<a href="' + F["file"] + '.ots">OpenTimestamps .ots</a>' if ots else "&mdash;")])}{tr(["Atlantic, Gulf and Pacific coasts (south of 56&deg;N)", FS["sealed"], str(FS["cutoff_id"]), f"{FS['n_cells']:,}", f'<code style="font-size:11.5px">{FS["sha256"]}</code>', ('<a href="' + FS["file"] + '.ots">OpenTimestamps .ots</a>' if os.path.exists(FS["file"] + ".ots") else "&mdash;")]) if FS else ""}</tbody></table></div>
  <p class="lede" style="font-size:13.5px">The second file, sealed a day later under the same rule, covers every chart-safe cell of the southern blocks (68 blocks, no route filter, inland rivers and lakes excluded because the gravity anchor does not apply there). It exists to make the test resolve faster: the Arctic produces ten to twenty danger notices between freeze-up and spring, the southern coasts about fifteen a month inside this coverage. Most southern notices fall in the St. Lawrence River and the Great Lakes, which are outside both files and do not count either way.</p>
  <p class="lede" style="font-size:13.5px"><b>The rule.</b> {F["rule"]}. Success is a share of notices in the top decile well above one in ten; the Wilson 95% interval is reported with it. Last season the same window (12 September to 30 November) produced 19 danger notices at these latitudes, so the first Arctic reading will be coarse and the test keeps accumulating through the 2027 season. Manifest <a href="forecast_danger_2026-09-12.json">forecast_danger_2026-09-12.json</a>; the full cell file (485 MB) is available on request and reproduces the hash.</p>{score_html}
</section>
'''
    anchor = '<section>\n  <div class="eyebrow">Exhibit J &mdash; sealed claims</div>'
    src = sub1(src, anchor, N + anchor)
    for f in ("forecast_danger_2026-09-12.json", "forecast_danger_2026-09-12.csv.ots", "prospective_score_2026-09-12.json", "forecast_danger_south_2026-09-13.json", "forecast_danger_south_2026-09-13.csv.ots", "prospective_score_2026-09-13.json"):
        if os.path.exists(f): shutil.copy(f, "pages_repo/" + f)

# --- Exhibit O: ships of opportunity
CS = load("csb_shelf_stats.json")
if CS:
    def row(label, r): return tr([label, str(r["n"]), f"{r['model']['median']:.1f} / {r['model']['within10']*100:.0f}%", f"{r['nearest']['median']:.1f} / {r['nearest']['within10']*100:.0f}%", f"{r['blend']['median']:.1f} / {r['blend']['within10']*100:.0f}%"])
    rows = row("All shelf cells", CS["all"]) + "".join(row(f"{k} km from a sounding", v) for k, v in CS["by_distance_km"].items()) + "".join(row(f"{k} m deep", v) for k, v in CS["by_depth_m"].items()) + "".join(row(k, v) for k, v in CS["by_region"].items())
    O = f'''<section>
  <div class="eyebrow">Exhibit O &mdash; ships of opportunity</div>
  <h2>Independent soundings nobody trained on: what cruise ships and yachts measured where the map had no sounding</h2>
  <p class="lede">The International Hydrographic Organization pools depth readings that ordinary vessels log while sailing. Every ping uploaded in 2026 was pulled ({CS["cells_unsounded_total"]:,} map cells with no charted sounding received at least three pings). The readings are raw, so each vessel was first checked against charted soundings and kept only if it agreed to within a few metres, with its draft offset removed: 44 of 82 vessels passed, and on charted cells their readings then sit 1.6 m from the chart. Cells where a vessel reported under 20 m over water a nearby survey measured at more than 100 m were dropped as sounder dropouts. What remains is {CS["shelf_cells"]:,} shelf cells (0&ndash;200 m) on the Pacific and Atlantic coasts. There is no Arctic in this pool yet: sealift and Arctic cruise operators do not contribute.</p>
  <div class="tblwrap"><table><thead>{tr(["Cells", "n", "Model: median error / within 10 m", "Nearest sounding", "Blend"], True)}</thead><tbody>{rows}</tbody></table></div>
  <p class="lede" style="font-size:13.5px">Two honest things. First, most of these cells sit within a kilometre of a charted sounding, because ships sail where surveys exist, and there the nearest sounding beats the model; the model only pulls ahead beyond a kilometre, where the corridor claims live. Second, that is a defect of the published map and it is now fixed: the blend column applies the distance weighting from Exhibit M (fitted on the Arctic benchmark, not on these cells) and matches the better of the two everywhere. File <a href="csb_shelf_stats.json">csb_shelf_stats.json</a>.</p>
</section>
'''
    anchor = '<section>\n  <div class="eyebrow">Exhibit J &mdash; sealed claims</div>'
    src = sub1(src, anchor, O + anchor); shutil.copy("csb_shelf_stats.json", "pages_repo/csb_shelf_stats.json")

# --- ships vs claims (Exhibit O addendum)
CV = load("candidates_vs_csb_summary.json")
if CV and CS:
    rc = CV["sealed_claim_refuted"]
    para = f'''
  <h3 style="font-size:19px;margin:22px 0 6px">Ships against the claims</h3>
  <p class="lede" style="font-size:14.5px">The same ship soundings were run against every hazard candidate and every sealed claim. One sealed claim is refuted: the {rc["region"]} claim at {rc["lat"]:.3f}&deg;N {abs(rc["lon"]):.3f}&deg;W predicted a {rc["predicted_m"]:.0f} m shoal where the chart reads about {rc["chart_m"]} m; {rc["pings_within_300m"]} ship soundings within 300 m read {rc["ping_depth_q10_q50_q90"][0]}&ndash;{rc["ping_depth_q10_q50_q90"][2]} m. It is wrong and stays on the sealed list marked as such. The other 39 sealed claims are in Arctic water with no ship traffic and remain untested. Of {CV["n_candidates"]:,} unsealed hazard candidates, {CV["n_with_pings"]} have at least five ship soundings within 300 m: {CV["refuted"]} are refuted, {CV["ambiguous"]} ambiguous, and none is a confirmed offshore shoal once bad loggers and coastal shallows are removed. Two honest readings follow. The hazard field over-predicts in charted, busy southern waters, which is where ships can check it; and ships choose safe water, so a sounding 300 m away does not rule out a narrow pinnacle. File <a href="candidates_vs_csb_summary.json">candidates_vs_csb_summary.json</a>.</p>'''
    src = src.replace('File <a href="csb_shelf_stats.json">csb_shelf_stats.json</a>.</p>\n</section>', 'File <a href="csb_shelf_stats.json">csb_shelf_stats.json</a>.</p>' + para + '\n</section>'); shutil.copy("candidates_vs_csb_summary.json", "pages_repo/candidates_vs_csb_summary.json")

# --- map version note (Exhibit M) + v6h ship test row
CSH = load("csb_shelf_stats_v6h.json")
note = '''
  <p class="lede" style="font-size:14.5px"><b>The corridor map layer is now the six-member map.</b> Six full-data models (the published one, two retrains, three seeds) each run with four-fold test-time augmentation, averaged, then blended with the nearest sounding by distance. Its held-out proxy is the three-member augmented ensemble with the same blend, {H6:.2f} m on the temporal benchmark against {H0:.1f} m for the published map; the six-member map itself cannot be scored there because its members saw every year of soundings.'''
hy = load("temporal_validation_hybrid_ens3tta.json"); base = load("temporal_validation_temporal_base.json")
if hy and base:
    note = note.replace("{H6:.2f}", f"{hy['overall']['mae_model']:.2f}").replace("{H0:.1f}", f"{base['overall']['mae_model']:.1f}")
    if CSH and CSH.get("all") and CS: note += f" On the ship soundings of Exhibit O it scores a median error of {CSH['all']['model']['median']:.1f} m and {CSH['all']['model']['within10']*100:.0f}% within 10 m at shelf cells with no charted sounding, against {CS['all']['model']['median']:.1f} m and {CS['all']['model']['within10']*100:.0f}% for the unblended three-member map. File <a href=\"csb_shelf_stats_v6h.json\">csb_shelf_stats_v6h.json</a>."; shutil.copy("csb_shelf_stats_v6h.json", "pages_repo/csb_shelf_stats_v6h.json")
    note += "</p>"
    i = src.find("Full size, full corpus, from scratch: + winter radar"); j = src.find("</table></div>", i) + len("</table></div>"); src = src[:j] + note + src[j:]

src = src.replace("atlas v7.3", "atlas v8.0")
open("churchill_atlas_v8.html", "w", encoding="utf-8").write(src); print("ATLAS_V8_DONE", len(src)//1024, "KB; extra rows", len(extra), "| N", bool(F))
