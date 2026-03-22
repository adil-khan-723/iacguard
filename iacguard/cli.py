import sys
import argparse
from iacguard import __version__
from iacguard.parser.plan_parser import load_plan, parse_changes
from iacguard.engine.runner import run_rules, summarize
from iacguard.output.terminal import print_output, print_no_changes
from iacguard.output.json_output import build_json


def cmd_plan(args):
    if not args.plan and not args.dir:
        print("[iacguard] ERROR: Provide --plan <path> or --dir <path>", file=sys.stderr)
        sys.exit(2)

    plan_path = args.plan
    if not plan_path and args.dir:
        import subprocess, tempfile, os
        from pathlib import Path
        tf_dir = Path(args.dir)
        out_file = tf_dir / "iacguard_plan.json"
        try:
            subprocess.run(["terraform", "plan", "-out=tfplan"], cwd=tf_dir, check=True, capture_output=True)
            subprocess.run(["terraform", "show", "-json", "tfplan"], cwd=tf_dir, check=True,
                           stdout=open(out_file, "w"))
            plan_path = str(out_file)
        except Exception as e:
            print(f"[iacguard] ERROR: Failed to generate plan from directory: {e}", file=sys.stderr)
            sys.exit(2)

    data    = load_plan(plan_path)
    changes = parse_changes(data)

    skipped = []
    if not args.region:
        skipped.append("Drift check     : SKIPPED (use --region to enable)")
    skipped.append("Checkov         : SKIPPED (not installed in v1)")

    if not changes:
        if args.ci:
            summary = {"critical":0,"high":0,"medium":0,"low":0,"resources_analyzed":0,"changes":0,"skipped":0}
            print(build_json([], summary, skipped, plan_path, no_changes=True))
        else:
            print_no_changes()
        sys.exit(0)

    findings = run_rules(changes)
    summary  = summarize(findings, changes)

    if args.ci:
        filtered = findings
        if args.severity:
            sf = args.severity.upper()
            order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            if sf in order:
                idx = order.index(sf)
                filtered = [f for f in findings if order.index(f.severity.value) <= idx]
        print(build_json(filtered, summary, skipped, plan_path))
    else:
        print_output(findings, summary, skipped, no_color=args.ci, severity_filter=args.severity)

    if summary["critical"] > 0:
        sys.exit(1)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        prog="iacguard",
        description="Terraform pre-apply risk and blast radius analyzer"
    )
    parser.add_argument("--version", action="version", version=f"iacguard {__version__}")

    sub = parser.add_subparsers(dest="command")

    # iacguard plan
    plan_p = sub.add_parser("plan", help="Analyze a Terraform plan for risks")
    plan_p.add_argument("--plan",     metavar="PATH",   help="Path to terraform plan JSON file")
    plan_p.add_argument("--dir",      metavar="PATH",   help="Terraform directory (auto-generates plan)")
    plan_p.add_argument("--ci",       action="store_true", help="CI mode: JSON output + exit codes")
    plan_p.add_argument("--severity", metavar="LEVEL",  help="Filter: critical, high, medium, low")
    plan_p.add_argument("--region",   metavar="REGION", help="AWS region (enables drift check)")
    plan_p.add_argument("--profile",  metavar="NAME",   help="AWS CLI profile")
    plan_p.add_argument("--no-aws",   action="store_true", help="Skip all AWS API calls")
    plan_p.add_argument("--explain",  action="store_true", help="AI explanation (requires ANTHROPIC_API_KEY)")

    args = parser.parse_args()

    if args.command == "plan":
        cmd_plan(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
