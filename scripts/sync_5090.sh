#!/usr/bin/env bash
set -Eeuo pipefail

# Safe Git/artifact exchange between the local workstation and the 5090 host.
# This script never force-pushes, deletes a remote branch, or rsyncs with --delete.

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
lab_repo=$(cd -- "$script_dir/.." && pwd)
sync_remote=${GSFL_SYNC_REMOTE:-colin-sync}
remote_host=${GSFL_5090_HOST:-colin}
remote_lab_root=${GSFL_5090_LAB_ROOT:-/home/intern/gs_floaterLab}

usage() {
    sed -n '/^# Usage:/,/^# End usage/{ /^# End usage/d; p; }' "$0" |
        sed -e 's/^# //' -e 's/^#$//'
}

# Usage:
#   scripts/sync_5090.sh status [all|lab|vigs]
#   scripts/sync_5090.sh fetch [all|lab|vigs]
#   scripts/sync_5090.sh new-work <lab|vigs> <topic> [base-branch]
#   scripts/sync_5090.sh publish <lab|vigs> [work/branch]
#   scripts/sync_5090.sh pull-artifacts <results/...|context/experiments/...>
#
# Environment overrides:
#   VIGS_REPO, GSFL_SYNC_REMOTE, GSFL_5090_HOST, GSFL_5090_LAB_ROOT
# End usage

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

find_vigs_repo() {
    local candidate
    if [[ -n ${VIGS_REPO:-} ]]; then
        candidate=$VIGS_REPO
    elif [[ -d /home/intern/VIGS-SLAM-custom/.git ]]; then
        candidate=/home/intern/VIGS-SLAM-custom
    else
        candidate=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM
    fi
    [[ -d "$candidate/.git" ]] || die "VIGS repository not found: $candidate"
    printf '%s\n' "$candidate"
}

repo_path() {
    case ${1:-} in
        lab) printf '%s\n' "$lab_repo" ;;
        vigs) find_vigs_repo ;;
        *) die "repository must be 'lab' or 'vigs'" ;;
    esac
}

for_each_repo() {
    local scope=$1
    shift
    case "$scope" in
        all)
            "$@" lab "$(repo_path lab)"
            "$@" vigs "$(repo_path vigs)"
            ;;
        lab|vigs) "$@" "$scope" "$(repo_path "$scope")" ;;
        *) die "scope must be all, lab, or vigs" ;;
    esac
}

require_sync_remote() {
    local path=$1
    git -C "$path" remote get-url "$sync_remote" >/dev/null 2>&1 ||
        die "$path has no '$sync_remote' remote; see context/SYNC_5090.md"
}

status_one() {
    local name=$1 path=$2 branch remote_ref counts
    require_sync_remote "$path"
    branch=$(git -C "$path" symbolic-ref --quiet --short HEAD || printf '(detached)')
    printf '\n[%s] %s\n' "$name" "$path"
    git -C "$path" status --short --branch --untracked-files=no
    printf 'sync URL: %s\n' "$(git -C "$path" remote get-url "$sync_remote")"
    if [[ "$branch" != '(detached)' ]]; then
        remote_ref="refs/remotes/$sync_remote/$branch"
        if git -C "$path" show-ref --verify --quiet "$remote_ref"; then
            counts=$(git -C "$path" rev-list --left-right --count "HEAD...$sync_remote/$branch")
            printf 'HEAD vs %s/%s: %s (local-only, remote-only)\n' \
                "$sync_remote" "$branch" "$counts"
        else
            printf 'HEAD vs %s/%s: remote-tracking ref not fetched yet\n' \
                "$sync_remote" "$branch"
        fi
    fi
}

fetch_one() {
    local name=$1 path=$2
    require_sync_remote "$path"
    printf '\n[%s] fetching refs only; worktree is unchanged\n' "$name"
    git -C "$path" fetch "$sync_remote"
}

require_clean_tracked() {
    local path=$1 dirty
    dirty=$(git -C "$path" status --porcelain=v1 --untracked-files=no)
    [[ -z "$dirty" ]] || {
        printf '%s\n' "$dirty" >&2
        die "tracked changes exist; commit or preserve them before switching/publishing"
    }
}

safe_component() {
    [[ $1 =~ ^[A-Za-z0-9._/-]+$ ]] || die "unsafe name: $1"
    [[ $1 != /* && $1 != *..* ]] || die "absolute paths and '..' are forbidden: $1"
}

new_work() {
    local name=$1 topic=$2 base=${3:-main} path machine branch
    path=$(repo_path "$name")
    require_sync_remote "$path"
    require_clean_tracked "$path"
    safe_component "$topic"
    safe_component "$base"
    machine=$(hostname -s | tr -cd 'A-Za-z0-9._-')
    branch="work/$machine/$topic"
    git -C "$path" fetch "$sync_remote"
    git -C "$path" show-ref --verify --quiet "refs/remotes/$sync_remote/$base" ||
        die "base branch does not exist: $sync_remote/$base"
    if git -C "$path" show-ref --verify --quiet "refs/heads/$branch"; then
        die "local branch already exists: $branch"
    fi
    git -C "$path" switch -c "$branch" "$sync_remote/$base"
    printf 'Created %s in %s\n' "$branch" "$path"
}

publish() {
    local name=$1 requested=${2:-} path branch target
    path=$(repo_path "$name")
    require_sync_remote "$path"
    require_clean_tracked "$path"
    branch=$(git -C "$path" symbolic-ref --quiet --short HEAD) ||
        die "detached HEAD cannot be published"
    target=${requested:-$branch}
    safe_component "$target"
    case "$target" in
        work/*|preserve/*) ;;
        *) die "publish target must begin with work/ or preserve/; main is integration-only" ;;
    esac
    git -C "$path" fetch "$sync_remote"
    git -C "$path" push "$sync_remote" "HEAD:refs/heads/$target"
    printf 'Published %s HEAD to %s/%s without force\n' "$name" "$sync_remote" "$target"
}

pull_artifacts() {
    local relative=$1 destination backup_stamp backup_root
    safe_component "$relative"
    case "$relative" in
        results/*|context/experiments/*) ;;
        *) die "artifact path must start with results/ or context/experiments/" ;;
    esac
    destination="$lab_repo/results/5090_mirror/$relative"
    backup_stamp=$(date +%Y%m%d-%H%M%S)
    backup_root="$lab_repo/results/5090_mirror/.previous/$backup_stamp/$relative"
    mkdir -p -- "$destination" "$backup_root"
    printf 'Pulling %s:%s/%s\n' "$remote_host" "$remote_lab_root" "$relative"
    printf 'Destination: %s\n' "$destination"
    printf 'Overwritten local files are backed up under: %s\n' "$backup_root"
    rsync -a --partial --backup --backup-dir="$backup_root" \
        "$remote_host:$remote_lab_root/$relative/" "$destination/"
    printf 'Done. No remote files were modified or deleted.\n'
}

command=${1:-help}
case "$command" in
    status)
        for_each_repo "${2:-all}" status_one
        ;;
    fetch)
        for_each_repo "${2:-all}" fetch_one
        ;;
    new-work)
        [[ $# -ge 3 && $# -le 4 ]] || die "new-work requires <lab|vigs> <topic> [base]"
        new_work "$2" "$3" "${4:-main}"
        ;;
    publish)
        [[ $# -ge 2 && $# -le 3 ]] || die "publish requires <lab|vigs> [work/branch]"
        publish "$2" "${3:-}"
        ;;
    pull-artifacts)
        [[ $# -eq 2 ]] || die "pull-artifacts requires one relative path"
        pull_artifacts "$2"
        ;;
    help|-h|--help)
        usage
        ;;
    *)
        usage >&2
        die "unknown command: $command"
        ;;
esac
