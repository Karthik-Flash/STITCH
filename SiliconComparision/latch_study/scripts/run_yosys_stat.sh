#!/usr/bin/env bash
set -euo pipefail

usage() {
    printf 'Usage: %s <design-dir> [--liberty <file>]\n' "$0" >&2
    exit 2
}

[[ $# -ge 1 ]] || usage
design_dir=$1
shift
liberty=
while [[ $# -gt 0 ]]; do
    case $1 in
        --liberty)
            [[ $# -ge 2 ]] || usage
            liberty=$2
            shift 2
            ;;
        *) usage ;;
    esac
done
[[ -d $design_dir ]] || { printf 'Not a directory: %s\n' "$design_dir" >&2; exit 2; }

design=${design_dir%/}
design=${design##*/}
case $design in
    mesh2x2) top=top_2x2_router ;;
    mesh3x3) top=top_3x3_router ;;
    mpsoc) top=main ;;
    *) printf 'Unknown design directory name: %s\n' "$design" >&2; exit 2 ;;
esac

yosys_bin=${STITCH_YOSYS:-}
if [[ -n $yosys_bin && ! -x $yosys_bin ]]; then
    yosys_bin=
fi
if [[ -z $yosys_bin && -n ${STITCH_SET4_OSSCAD:-} ]]; then
    for candidate in "$STITCH_SET4_OSSCAD/oss-cad-suite/bin/yosys" "$STITCH_SET4_OSSCAD/bin/yosys"; do
        if [[ -x $candidate ]]; then
            yosys_bin=$candidate
            break
        fi
    done
fi
if [[ -z $yosys_bin ]]; then
    yosys_bin=$(command -v yosys || true)
fi
[[ -n $yosys_bin && -x $yosys_bin ]] || { printf 'Yosys not found. Set STITCH_SET4_OSSCAD or STITCH_YOSYS.\n' >&2; exit 127; }
[[ -z $liberty || -f $liberty ]] || { printf 'Liberty file not found: %s\n' "$liberty" >&2; exit 2; }

mapfile -t sources < <(find "$design_dir" -maxdepth 1 -type f -name '*.v' -printf '%f\n' | sort)
[[ ${#sources[@]} -gt 0 ]] || { printf 'No Verilog sources in %s\n' "$design_dir" >&2; exit 2; }
read_script="read_verilog ${sources[*]}; hierarchy -check -top $top; synth -top $top; check; stat -top $top"
if [[ -n $liberty ]]; then
    read_script="read_verilog ${sources[*]}; hierarchy -check -top $top; synth -top $top; check; stat -liberty $liberty -top $top"
fi

log_file=$(mktemp)
stat_file=$(mktemp)
trap 'rm -f "$log_file" "$stat_file"' EXIT
printf 'Yosys: %s\n' "$($yosys_bin -V)"
if ! (cd "$design_dir" && "$yosys_bin" -p "$read_script") >"$log_file" 2>&1; then
    cat "$log_file"
    exit 1
fi
awk '/^=== design hierarchy ===/ {section=$0; active=1; next} active {section=section ORS $0} END {print section}' "$log_file" > "$stat_file"
read -r total_cells latch_cells flop_cells < <(awk '
    {
        type=""; count=""
        if ($1 ~ /^[0-9]+$/ && $2 ~ /^\$_?/) { count=$1; type=$2 }
        else if ($1 ~ /^\$_?/ && $NF ~ /^[0-9]+$/) { type=$1; count=$NF }
        if (type != "") {
            total += count
            if (type ~ /^\$_?DLATCH/) latches += count
            if (tolower(type) ~ /dff/) flops += count
        }
    }
    END { printf "%d %d %d\n", total, latches, flops }
' "$stat_file")
printf 'Total cells: %s\nLatch cells: %s\nFlop cells: %s\n' "$total_cells" "$latch_cells" "$flop_cells"
cat "$stat_file"