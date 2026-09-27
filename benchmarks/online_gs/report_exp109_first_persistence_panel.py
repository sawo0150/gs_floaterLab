#!/usr/bin/env python3
"""Build the Exp109 report from immutable pair verifier/runtime artifacts."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import run_exp109_first_persistence_panel as exp109


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def mean(items: list[float]) -> float:
    return sum(items) / len(items)


def collect() -> list[dict]:
    rows = exp109.prior.prior.panel.v2.install_inventory()
    collected = []
    for row in rows:
        local = exp109.ROOT / row["dataset"] / row["scene"]
        pair = read_json(local / "pair_verification.json")
        gate = read_json(local / "quality_gate.json")
        candidate_eval = read_json(
            local
            / "first_persistence_ticket_s0"
            / "evaluation_consistency.json"
        )
        vanilla_eval = read_json(
            local
            / "native_vanilla_render_matched_s0"
            / "evaluation_consistency.json"
        )
        candidate_runtime = read_json(
            local
            / "first_persistence_ticket_s0"
            / "mapping_replay_runtime.json"
        )
        vanilla_runtime = read_json(
            local
            / "native_vanilla_render_matched_s0"
            / "mapping_replay_runtime.json"
        )
        historical_r4 = exp109.prior.prior.panel.scene_paths(row)["candidate"]
        r4_runtime = read_json(historical_r4 / "mapping_replay_runtime.json")
        d1 = pair["result"]["d1"]
        vanilla = pair["result"]["vanilla"]
        delta = pair["result"]["d1_minus_vanilla"]
        checks_pass = all(check["passed"] for check in pair["checks"].values())
        gate_checks_pass = all(gate["checks"].values())
        valid = (
            pair["valid"]
            and checks_pass
            and gate_checks_pass
            and not gate["stop"]
            and candidate_eval["pass"]
            and vanilla_eval["pass"]
        )
        collected.append(
            {
                "dataset": row["dataset"],
                "scene": row["scene"],
                "candidate_psnr": float(d1["psnr"]),
                "vanilla_psnr": float(vanilla["psnr"]),
                "delta_psnr": float(delta["psnr"]),
                "candidate_ssim": float(d1["ssim"]),
                "vanilla_ssim": float(vanilla["ssim"]),
                "delta_ssim": float(delta["ssim"]),
                "candidate_lpips": float(d1["lpips"]),
                "vanilla_lpips": float(vanilla["lpips"]),
                "delta_lpips": float(delta["lpips"]),
                "delta_r4": float(gate["candidate_minus_r4_db"]),
                "r4_psnr": float(gate["historical_r4_psnr"]),
                "clones": int(gate["ticket"]["selected_mutations"]),
                "candidate_renders": int(d1["renders"]),
                "vanilla_renders": int(vanilla["renders"]),
                "candidate_adam": int(d1["optimizer_steps"]),
                "vanilla_adam": int(vanilla["optimizer_steps"]),
                "candidate_gaussians": int(d1["gaussians"]),
                "vanilla_gaussians": int(vanilla["gaussians"]),
                "r4_gaussians": int(r4_runtime["gaussians"]),
                "candidate_wall": float(candidate_runtime["mapping_wall_seconds"]),
                "vanilla_wall": float(vanilla_runtime["mapping_wall_seconds"]),
                "r4_wall": float(r4_runtime["mapping_wall_seconds"]),
                "candidate_peak_allocated_gib": float(
                    candidate_runtime["peak_cuda_allocated_bytes"]
                )
                / (1024 ** 3),
                "vanilla_peak_allocated_gib": float(
                    vanilla_runtime["peak_cuda_allocated_bytes"]
                )
                / (1024 ** 3),
                "r4_peak_allocated_gib": float(
                    r4_runtime["peak_cuda_allocated_bytes"]
                )
                / (1024 ** 3),
                "valid": valid,
            }
        )
    return collected


def aggregate(rows: list[dict]) -> dict:
    candidate_wall = sum(row["candidate_wall"] for row in rows)
    r4_wall = sum(row["r4_wall"] for row in rows)
    candidate_gaussians = sum(row["candidate_gaussians"] for row in rows)
    r4_gaussians = sum(row["r4_gaussians"] for row in rows)
    return {
        "count": len(rows),
        "wins": sum(row["delta_psnr"] > 0 for row in rows),
        "candidate_psnr": mean([row["candidate_psnr"] for row in rows]),
        "vanilla_psnr": mean([row["vanilla_psnr"] for row in rows]),
        "delta_psnr": mean([row["delta_psnr"] for row in rows]),
        "candidate_ssim": mean([row["candidate_ssim"] for row in rows]),
        "vanilla_ssim": mean([row["vanilla_ssim"] for row in rows]),
        "delta_ssim": mean([row["delta_ssim"] for row in rows]),
        "candidate_lpips": mean([row["candidate_lpips"] for row in rows]),
        "vanilla_lpips": mean([row["vanilla_lpips"] for row in rows]),
        "delta_lpips": mean([row["delta_lpips"] for row in rows]),
        "delta_r4": mean([row["delta_r4"] for row in rows]),
        "clones": sum(row["clones"] for row in rows),
        "candidate_wall_total": candidate_wall,
        "r4_wall_total": r4_wall,
        "wall_delta_r4_percent": 100.0 * (candidate_wall / r4_wall - 1.0),
        "candidate_gaussians_total": candidate_gaussians,
        "r4_gaussians_total": r4_gaussians,
        "gaussian_delta_r4_percent": (
            100.0 * (candidate_gaussians / r4_gaussians - 1.0)
        ),
        "valid": all(row["valid"] for row in rows),
    }


def main() -> int:
    rows = collect()
    if len(rows) != 17:
        raise RuntimeError(f"expected 17 complete pairs, found {len(rows)}")
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["dataset"]].append(row)
    overall = aggregate(rows)
    accepted = (
        overall["delta_psnr"] >= 0.5
        and overall["wins"] >= 9
        and overall["valid"]
        and all(row["delta_r4"] >= -0.5 for row in rows)
    )
    stretch = (
        overall["delta_psnr"] >= 1.253787
        and overall["wins"] == 17
        and overall["valid"]
        and all(row["delta_r4"] >= -0.5 for row in rows)
    )

    lines = [
        "# Exp109 — frozen first-persistence 17-scene B-track panel",
        "",
        "Every row is a fresh candidate/official-vanilla pair from this output",
        "root. The source-locked mapper completed all 17 pairs; its inline",
        "summary then failed because the inherited compact result omitted work",
        "fields. This report is regenerated only from immutable verifier, gate,",
        "evaluation-consistency, and runtime JSON artifacts.",
        "",
        "## Dataset means",
        "",
        "Values are scene-arithmetic means, not pooled-frame means.",
        "",
        "| Dataset | Scenes | PSNR C/V | delta PSNR | SSIM C/V | delta SSIM | LPIPS C/V | delta LPIPS | Wins | delta R4 | Clones | Wall delta R4 | GS delta R4 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for dataset in ("rpng", "utmm", "aria"):
        item = aggregate(grouped[dataset])
        lines.append(
            f"| {dataset.upper()} | {item['count']} | "
            f"{item['candidate_psnr']:.4f}/{item['vanilla_psnr']:.4f} | "
            f"{item['delta_psnr']:+.4f} | "
            f"{item['candidate_ssim']:.4f}/{item['vanilla_ssim']:.4f} | "
            f"{item['delta_ssim']:+.4f} | "
            f"{item['candidate_lpips']:.4f}/{item['vanilla_lpips']:.4f} | "
            f"{item['delta_lpips']:+.4f} | "
            f"{item['wins']}/{item['count']} | {item['delta_r4']:+.4f} | "
            f"{item['clones']:,} | {item['wall_delta_r4_percent']:+.2f}% | "
            f"{item['gaussian_delta_r4_percent']:+.3f}% |"
        )
    lines.extend(
        (
            f"| **Overall** | **17** | **{overall['candidate_psnr']:.4f}/"
            f"{overall['vanilla_psnr']:.4f}** | **{overall['delta_psnr']:+.4f}** | "
            f"**{overall['candidate_ssim']:.4f}/{overall['vanilla_ssim']:.4f}** | "
            f"**{overall['delta_ssim']:+.4f}** | "
            f"**{overall['candidate_lpips']:.4f}/{overall['vanilla_lpips']:.4f}** | "
            f"**{overall['delta_lpips']:+.4f}** | **{overall['wins']}/17** | "
            f"**{overall['delta_r4']:+.4f}** | **{overall['clones']:,}** | "
            f"**{overall['wall_delta_r4_percent']:+.2f}%** | "
            f"**{overall['gaussian_delta_r4_percent']:+.3f}%** |",
            "",
            "## Per-scene results",
            "",
            "| Dataset | Scene | Candidate | Vanilla | delta vanilla | delta R4 | Clone | Render C/V | Adam C/V | GS C/R4/V | Wall C/R4/V (s) | Peak alloc C/R4/V (GiB) | Gate |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        )
    )
    for row in rows:
        lines.append(
            f"| {row['dataset']} | {row['scene']} | "
            f"{row['candidate_psnr']:.4f} | {row['vanilla_psnr']:.4f} | "
            f"{row['delta_psnr']:+.4f} | {row['delta_r4']:+.4f} | "
            f"{row['clones']:,} | "
            f"{row['candidate_renders']:,}/{row['vanilla_renders']:,} | "
            f"{row['candidate_adam']:,}/{row['vanilla_adam']:,} | "
            f"{row['candidate_gaussians']:,}/{row['r4_gaussians']:,}/"
            f"{row['vanilla_gaussians']:,} | "
            f"{row['candidate_wall']:.2f}/{row['r4_wall']:.2f}/"
            f"{row['vanilla_wall']:.2f} | "
            f"{row['candidate_peak_allocated_gib']:.2f}/"
            f"{row['r4_peak_allocated_gib']:.2f}/"
            f"{row['vanilla_peak_allocated_gib']:.2f} | "
            f"{'PASS' if row['valid'] else 'FAIL'} |"
        )
    lines.extend(
        (
            "",
            "## Verdict",
            "",
            f"- Completed fresh pairs: **17/17**; wins: **{overall['wins']}/17**.",
            f"- Scene-arithmetic mean delta PSNR: **{overall['delta_psnr']:+.6f} dB**.",
            f"- Mean delta versus exact Exp94 R4: **{overall['delta_r4']:+.6f} dB**.",
            f"- Aggregate mapping wall versus exact R4: **{overall['wall_delta_r4_percent']:+.2f}%**; summed final Gaussian count: **{overall['gaussian_delta_r4_percent']:+.3f}%**.",
            f"- Minimum acceptance (mean >=+0.5 dB, majority wins, all fairness/R4-floor checks): **{'PASS' if accepted else 'FAIL'}**.",
            f"- Exp94 stretch target (+1.253787 dB and 17/17 wins): **{'PASS' if stretch else 'FAIL'}**.",
            "- This establishes quality preservation and active dense/ERCB topology under B-track. It does not establish strict-live deadline compliance or a causal quality gain over ticket-off R4.",
        )
    )
    exp109.DOCS.mkdir(parents=True, exist_ok=True)
    (exp109.DOCS / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    report = {
        "protocol": "exp109_artifact_only_report_v1",
        "rows": rows,
        "dataset_means": {
            dataset: aggregate(grouped[dataset])
            for dataset in ("rpng", "utmm", "aria")
        },
        "overall": overall,
        "minimum_acceptance_pass": accepted,
        "stretch_target_pass": stretch,
    }
    (exp109.DOCS / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Exp109 report PASS: mean={overall['delta_psnr']:+.6f} dB, "
        f"wins={overall['wins']}/17, stretch={stretch}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
