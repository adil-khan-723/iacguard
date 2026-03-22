import json
import sys
from pathlib import Path
from typing import Optional
from iacguard.rules.base import Action, ResourceChange


ACTIVE_ACTIONS = {
    ("create",)               : Action.CREATE,
    ("update",)               : Action.UPDATE,
    ("delete",)               : Action.DESTROY,
    ("delete", "create")      : Action.REPLACE,
    ("create", "delete")      : Action.REPLACE,
}

SKIP_ACTIONS = {("no-op",), ("read",)}


def normalize_action(raw: list) -> Optional[Action]:
    key = tuple(sorted(raw)) if len(raw) > 1 else tuple(raw)
    # handle delete+create order variants
    if set(raw) == {"delete", "create"}:
        return Action.REPLACE
    return ACTIVE_ACTIONS.get(tuple(raw))


def parse_module(address: str) -> Optional[str]:
    parts = address.split(".")
    if parts[0] == "module":
        return parts[1]
    return None


def short_name(address: str) -> str:
    parts = address.split(".")
    if parts[0] == "module":
        # module.name.resource_type.resource_name
        return ".".join(parts[2:]) if len(parts) >= 4 else address
    return address


def load_plan(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"[iacguard] ERROR: Plan file not found: {path}", file=sys.stderr)
        print(f"[iacguard] Hint: Run 'terraform plan -out=tfplan && terraform show -json tfplan > plan.json'", file=sys.stderr)
        sys.exit(2)

    try:
        with open(p) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[iacguard] ERROR: File is not valid JSON: {path}", file=sys.stderr)
        print(f"[iacguard] Detail: {e}", file=sys.stderr)
        sys.exit(2)

    if "resource_changes" not in data and "planned_values" not in data:
        print(f"[iacguard] ERROR: File does not look like a terraform plan JSON: {path}", file=sys.stderr)
        print(f"[iacguard] Hint: Make sure you ran 'terraform show -json tfplan', not just 'terraform show'", file=sys.stderr)
        sys.exit(2)

    return data


def parse_changes(data: dict) -> list:
    raw_changes = data.get("resource_changes", [])
    changes = []
    short_names_seen = {}

    for rc in raw_changes:
        # only managed resources
        if rc.get("mode") != "managed":
            continue

        raw_actions = rc.get("change", {}).get("actions", ["no-op"])
        action_tuple = tuple(raw_actions)

        # skip no-op and read
        if action_tuple in SKIP_ACTIONS:
            continue

        action = normalize_action(raw_actions)
        if action is None:
            print(f"[iacguard] WARNING: Unknown action type {raw_actions} on {rc.get('address')} — skipping", file=sys.stderr)
            continue

        address      = rc.get("address", "unknown")
        resource_type= rc.get("type", "unknown")
        name         = rc.get("name", "unknown")
        module       = parse_module(address)
        change       = rc.get("change", {})
        before       = change.get("before")
        after        = change.get("after")
        after_unknown= change.get("after_unknown", {})
        replacing    = change.get("replacing", False) or (set(raw_actions) == {"delete", "create"})

        sname = short_name(address)
        short_names_seen[sname] = short_names_seen.get(sname, 0) + 1

        changes.append(ResourceChange(
            address=address,
            module=module,
            resource_type=resource_type,
            name=name,
            action=action,
            before=before,
            after=after,
            after_unknown=after_unknown if isinstance(after_unknown, dict) else {},
            replacing=replacing,
        ))

    # flag duplicates so output layer can decide to show full address
    for c in changes:
        sname = short_name(c.address)
        c._has_duplicate = short_names_seen.get(sname, 0) > 1

    return changes
