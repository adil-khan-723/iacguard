import sys
from iacguard.rules.base import Finding, Severity

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    HAS_COLOR = True
    SEV_COLOR = {
        Severity.CRITICAL: Fore.RED,
        Severity.HIGH:     Fore.YELLOW,
        Severity.MEDIUM:   Fore.CYAN,
        Severity.LOW:      Fore.GREEN,
    }
    RESET = Style.RESET_ALL
except ImportError:
    HAS_COLOR = False
    SEV_COLOR = {
        Severity.CRITICAL: "\033[91m",
        Severity.HIGH:     "\033[93m",
        Severity.MEDIUM:   "\033[94m",
        Severity.LOW:      "\033[92m",
    }
    RESET = "\033[0m"

LINE = "─" * 57
NUM_RULES = 3  # RDS001, SG001, S3001


def _sev(f: Finding, no_color: bool) -> str:
    if no_color:
        return f"{f.severity.value:<8}"
    color = SEV_COLOR.get(f.severity, "")
    return f"{color}{f.severity.value:<8}{RESET}"


def print_output(findings: list, summary: dict, skipped: list,
                 no_color: bool = False, severity_filter: str = None):
    out = sys.stdout

    if severity_filter:
        order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        sf = severity_filter.upper()
        if sf in order:
            idx = order.index(sf)
            findings = [f for f in findings if order.index(f.severity.value) <= idx]

    print(f"\niacguard plan results", file=out)
    print(LINE, file=out)
    print(
        f"Critical : {summary['critical']}  |  "
        f"High : {summary['high']}  |  "
        f"Medium : {summary['medium']}  |  "
        f"Low : {summary['low']}",
        file=out,
    )
    print(
        f"Resources analyzed : {summary['resources_analyzed']}  |  "
        f"Changes : {summary['changes']}",
        file=out,
    )
    print(LINE, file=out)

    if not findings:
        print("\n  No issues found.\n", file=out)
    else:
        print("", file=out)
        for f in findings:
            sev = _sev(f, no_color)
            print(f"  {sev}  {f.rule_id}  {f.resource_address}  [{f.action.value}]", file=out)
            print(f"           {f.message}", file=out)
            if f.blast_radius:
                print(f"           Blast radius: {len(f.blast_radius)} resource(s) depend on this", file=out)
            print("", file=out)

    print(LINE, file=out)
    print(f"[iacguard] Rules checked   : {NUM_RULES}", file=out)
    for s in skipped:
        print(f"[iacguard] {s}", file=out)
    print(LINE, file=out)
    print("", file=out)


def print_no_changes():
    print(f"\niacguard plan results")
    print(LINE)
    print("  No infrastructure changes detected.")
    print(LINE)
    print("")
