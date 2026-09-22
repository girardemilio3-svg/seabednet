#!/bin/sh
# Publish atlas v8.1 once the v6h terrain tiles and the v6h ship test are done.
cd "$(dirname "$0")/../.."
until grep -q TILES_EXIT make_tiles_v6h.log 2>/dev/null && grep -q CSB_EVAL2_EXIT csb_eval2_v6h.log 2>/dev/null; do sleep 60; done
echo "START $(date)" >> publish_v8.log
grep -q "TILES_EXIT 0" make_tiles_v6h.log || { echo "TILES FAILED" >> publish_v8.log; exit 1; }
python3 build_atlas_v8.py >> publish_v8.log 2>&1
rm -rf pages_repo/map/tiles/terrain && cp -r map/tiles/terrain pages_repo/map/tiles/terrain
cp churchill_atlas_v8.html pages_repo/index.html
cd pages_repo && git add -A map/tiles/terrain index.html *.json 2>/dev/null; git commit -qm "Atlas v8.1: six-member augmented + blended map as the corridor layer; ships vs claims (one sealed claim refuted), laser second pass, ship test of the new map

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01DtgnKmLqL1Zqd4bMGKZkX1" >> ../publish_v8.log 2>&1 && git push -q >> ../publish_v8.log 2>&1
echo "PUBLISH_DONE $(date) $(git log --oneline -1)" >> ../publish_v8.log
