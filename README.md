# IACGuard

**Terraform pre-apply risk and blast radius analyzer**

> Know the blast radius of every Terraform change before you apply it.

IACGuard reads your Terraform plan, runs deterministic safety rules against
every planned change, and tells you what is dangerous — before anything is
touched. Full CI/CD support via JSON output and exit codes.

---

## Install

```bash
pip install iacguard
```

## Quick start

```bash
# Generate a plan file
terraform plan -out=tfplan
terraform show -json tfplan > plan.json

# Analyze it
iacguard plan --plan plan.json

# CI mode (JSON output + exit codes)
iacguard plan --plan plan.json --ci
```

## What it checks (v0.1.0)

| Rule   | Severity | What it detects |
|--------|----------|-----------------|
| RDS001 | CRITICAL | RDS instance being replaced (data loss risk) |
| SG001  | CRITICAL | SSH port 22 open to 0.0.0.0/0 or ::/0 |
| S3001  | MEDIUM   | S3 bucket with no explicit public access block |

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | No critical findings — safe to proceed |
| 1    | Critical findings found — review before applying |
| 2    | Tool error (bad file, parse failure) |

## Flags

```
--plan PATH      Path to terraform plan JSON file
--dir  PATH      Terraform directory (auto-generates plan)
--ci             JSON output + exit codes (for pipelines)
--severity LEVEL Show only: critical, high, medium, low
--no-aws         Skip AWS API calls
--explain        AI explanation (requires ANTHROPIC_API_KEY)
```

## GitHub Actions example

```yaml
- name: IACGuard risk check
  run: |
    pip install iacguard
    terraform show -json tfplan > plan.json
    iacguard plan --plan plan.json --ci
```

## Architecture

IACGuard is 100% deterministic. Rules are pure Python functions —
they fire the same way every time. AI (optional `--explain` flag)
only explains findings after the rule engine has already decided.
AI never decides risk level and never runs in CI mode.
