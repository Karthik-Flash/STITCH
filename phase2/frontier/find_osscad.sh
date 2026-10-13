#!/bin/bash
# Locate the oss-cad-suite release matching the HPC build (read-only GitHub API queries).
api() { curl -s -H "Accept: application/vnd.github+json" "https://api.github.com/$1"; }
for c in "YosysHQ/yosys 150c32b03" "verilator/verilator 1aa87913c" "steveicarus/iverilog c9ed76463"; do
  set -- $c
  api "repos/$1/commits/$2" | python3 -c "import json,sys; d=json.load(sys.stdin); print('$1', d.get('sha','?')[:12], d.get('commit',{}).get('committer',{}).get('date'), d.get('message','')[:80])"
done
api "repos/YosysHQ/oss-cad-suite-build/releases?per_page=30" | python3 -c "
import json,sys
for r in json.load(sys.stdin):
    a=[x for x in r['assets'] if 'linux-x64' in x['name']]
    print(r['tag_name'], r['published_at'], [(x['name'], x['size']//2**20) for x in a])"
