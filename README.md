# IACGuard

> **Terraform pre-apply risk and blast radius analyzer**

Know the blast radius of every Terraform change before you apply it.

IACGuard is a command-line tool that reads your Terraform plan, runs deterministic safety rules against every planned change, and tells you exactly what is dangerous — before anything is touched. It supports CI/CD pipelines natively via JSON output and exit codes.

```
iacguard plan results
─────────────────────────────────────────────────────────
Critical : 1  |  High : 0  |  Medium : 0  |  Low : 0
Resources analyzed : 5  |  Changes : 5
─────────────────────────────────────────────────────────

  CRITICAL  SG001  aws_vpc_security_group_ingress_rule.sg_inbound_ssh  [CREATE]
           Security group ingress rule 'sg_inbound_ssh' allows SSH (port 22)
           from the entire internet (0.0.0.0/0 or ::/0).

─────────────────────────────────────────────────────────
[iacguard] Rules checked   : 3
[iacguard] Drift check     : SKIPPED (use --region to enable)
[iacguard] Checkov         : SKIPPED (not installed in v1)
─────────────────────────────────────────────────────────
```

---

## Why IACGuard

Before applying any Terraform change, DevOps engineers today:

- Read hundreds of lines of `terraform plan` output manually
- Switch to the AWS console to check security settings
- Guess at blast radius — what breaks if this change fails
- Hope nothing goes wrong at 2am

IACGuard replaces this with one command that catches real problems before `terraform apply` runs.

**This is not an AI tool.** Detection is 100% deterministic — rules are pure Python functions that fire the same way every time. AI is an optional explanation layer only, never detection. If IACGuard exits with code 1 in your pipeline, it is because a rule fired — not because a model happened to call something critical today.

---

## Requirements

- Python 3.9 or higher
- Terraform 1.0+ installed and in PATH
- AWS CLI configured (for drift detection — optional in v0.1.0)

---

## Installation

```bash
pip install iacguard
```

Or install from source:

```bash
git clone https://github.com/adil-khan-723/iacguard.git
cd iacguard
pip install -e .
```

Verify the install:

```bash
iacguard --version
```

---

## Quick start

**Step 1 — Generate a Terraform plan file**

```bash
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
```

**Step 2 — Run IACGuard**

```bash
iacguard plan --plan plan.json
```

**Step 3 — Use in CI/CD**

```bash
iacguard plan --plan plan.json --ci
echo "Exit code: $?"
```

Exit code 0 = safe to proceed. Exit code 1 = critical findings, block the deployment.

---

## Commands

### `iacguard plan`

Analyzes a Terraform plan file and runs all rules against every planned change.

```bash
# Analyze a plan JSON file
iacguard plan --plan ./plan.json

# Point at a Terraform directory (auto-generates plan)
iacguard plan --dir ./infra/

# CI mode — JSON output + exit codes
iacguard plan --plan ./plan.json --ci

# Show only critical findings
iacguard plan --plan ./plan.json --severity critical

# With AI explanation (requires ANTHROPIC_API_KEY)
iacguard plan --plan ./plan.json --explain
```

---

## Flags

| Flag | Description |
|------|-------------|
| `--plan PATH` | Path to terraform plan JSON file (from `terraform show -json`) |
| `--dir PATH` | Terraform directory — auto-generates plan using terraform CLI |
| `--ci` | CI mode: JSON output to stdout, exit codes, no color |
| `--severity LEVEL` | Filter output: `critical`, `high`, `medium`, `low` |
| `--region REGION` | AWS region — enables drift detection |
| `--profile NAME` | AWS CLI profile to use |
| `--no-aws` | Explicitly skip all AWS API calls |
| `--explain` | AI plain-English explanation of findings (requires `ANTHROPIC_API_KEY`) |
| `--version` | Print version and exit |

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | No critical findings — safe to proceed with `terraform apply` |
| `1` | One or more critical findings — review before applying |
| `2` | Tool error — bad file path, invalid JSON, parse failure |

---

## Rules

All rules are deterministic. They fire the same way every time on the same input. No AI is involved in detection.

| Rule ID | Severity | Resource types checked | What it detects |
|---------|----------|------------------------|-----------------|
| `RDS001` | CRITICAL | `aws_db_instance`, `aws_rds_cluster` | RDS instance being replaced — potential data loss and downtime |
| `SG001` | CRITICAL | `aws_security_group`, `aws_security_group_rule`, `aws_vpc_security_group_ingress_rule` | SSH port 22 open to 0.0.0.0/0 or ::/0 |
| `S3001` | MEDIUM | `aws_s3_bucket` | S3 bucket created without explicit `aws_s3_bucket_public_access_block` |

### RDS001 — RDS replacement

Detects when an RDS instance or cluster is being replaced rather than updated in place. A replacement means the database is deleted and recreated — any data written between deletion and restore from snapshot will be lost.

**Triggers on:** `actions: ["delete", "create"]` or `change.replacing == true` on `aws_db_instance` or `aws_rds_cluster`

**Does not trigger on:** in-place updates (`actions: ["update"]`) — parameter changes, backup window changes etc.

### SG001 — SSH open to the internet

Detects security group ingress rules that allow SSH access (port 22) from any IP address on the internet. Covers all three AWS provider resource types for security group rules including the newer `aws_vpc_security_group_ingress_rule` resource introduced in hashicorp/aws provider v5+.

**Covers:**
- `aws_security_group` with inline ingress blocks
- `aws_security_group_rule` with `type = "ingress"`
- `aws_vpc_security_group_ingress_rule` (AWS provider v5+)

**Checks:** IPv4 (`0.0.0.0/0`) and IPv6 (`::/0`) CIDRs. Checks port ranges correctly — fires if 22 falls anywhere within `from_port` to `to_port`.

**Does not trigger on:** egress rules (open egress to 0.0.0.0/0 is standard AWS practice), restricted CIDRs like `10.0.0.0/8`.

### S3001 — Missing public access block

Detects S3 buckets being created without an explicit `aws_s3_bucket_public_access_block` resource in the same plan. Severity is Medium — not Critical — because account-level Block Public Access settings may still protect the bucket. The finding message states this clearly.

**Does not trigger on:** existing buckets being updated, buckets where a public access block resource is present in the same plan.

---

## CI/CD Integration

### GitHub Actions

```yaml
name: IACGuard risk check

on:
  pull_request:
    branches: [main]

jobs:
  iacguard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Terraform init and plan
        run: |
          terraform init
          terraform plan -out=tfplan
          terraform show -json tfplan > plan.json
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

      - name: Install IACGuard
        run: pip install iacguard

      - name: Run IACGuard
        run: iacguard plan --plan plan.json --ci
```

When a Critical finding is detected, the workflow exits with code 1 and the PR is blocked automatically.

### GitLab CI

```yaml
iacguard:
  stage: validate
  script:
    - pip install iacguard
    - terraform init
    - terraform plan -out=tfplan
    - terraform show -json tfplan > plan.json
    - iacguard plan --plan plan.json --ci
```

### Jenkins

```groovy
stage('IACGuard') {
    steps {
        sh '''
            pip install iacguard
            terraform show -json tfplan > plan.json
            iacguard plan --plan plan.json --ci
        '''
    }
}
```

---

## CI JSON output schema

When running with `--ci`, IACGuard outputs a structured JSON payload to stdout. This schema is stable — field names and types will not change without a version bump.

```json
{
  "iacguard_version": "0.1.0",
  "plan_file": "./plan.json",
  "no_changes": false,
  "summary": {
    "critical": 1,
    "high": 0,
    "medium": 0,
    "low": 0,
    "resources_analyzed": 5,
    "changes": 5,
    "skipped": 0
  },
  "findings": [
    {
      "rule_id": "SG001",
      "severity": "CRITICAL",
      "resource_address": "aws_vpc_security_group_ingress_rule.sg_inbound_ssh",
      "resource_type": "aws_vpc_security_group_ingress_rule",
      "resource_name": "sg_inbound_ssh",
      "action": "CREATE",
      "message": "Security group ingress rule 'sg_inbound_ssh' allows SSH (port 22) from the entire internet (0.0.0.0/0 or ::/0).",
      "recommendation": "Restrict SSH access to known internal CIDR ranges only. Never expose port 22 to 0.0.0.0/0 in production.",
      "blast_radius": []
    }
  ],
  "errors": [],
  "skipped_sections": [
    "Drift check : SKIPPED (use --region to enable)",
    "Checkov     : SKIPPED (not installed in v1)"
  ]
}
```

---

## How it works

IACGuard is read-only. It never modifies, creates, or destroys any infrastructure.

```
terraform show -json tfplan > plan.json
        │
        ▼
   Plan parser
   ─────────────────────────────────────────
   • Loads plan JSON
   • Filters to managed resources only
   • Normalizes action types
     (create / update / destroy / replace)
   • Handles module paths
   • Handles null before/after values
        │
        ▼
   Rule engine (deterministic)
   ─────────────────────────────────────────
   • RDS001 — database replacement
   • SG001  — SSH open to internet
   • S3001  — missing public access block
   • Each rule is an independent function
   • No shared state between rules
        │
        ▼
   Output
   ─────────────────────────────────────────
   • Terminal: color-coded human output
   • CI mode:  JSON + exit codes
   • Optional: AI explanation (--explain)
```

**AI placement:** The optional `--explain` flag calls the Claude API to generate plain-English explanations of findings that the rule engine already found. AI never decides what is risky, never triggers exit codes, and never runs in `--ci` mode.

---

## Project structure

```
iacguard/
├── iacguard/
│   ├── cli.py                 Entry point, argument parsing
│   ├── parser/
│   │   └── plan_parser.py     Terraform plan JSON parser
│   ├── rules/
│   │   ├── base.py            Rule base class and data models
│   │   ├── rds001.py          RDS replacement rule
│   │   ├── sg001.py           SSH open to world rule
│   │   └── s3001.py           S3 public access block rule
│   ├── engine/
│   │   └── runner.py          Runs all rules, sorts findings
│   └── output/
│       ├── terminal.py        Human-readable colored output
│       └── json_output.py     CI JSON formatter
└── tests/
    ├── fixtures/              Real Terraform plan JSON files
    └── test_*.py              One test file per rule
```

---

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

Expected output: 15 passed.

---

## Compared to similar tools

| | IACGuard | Checkov | tfsec | Infracost |
|--|--|--|--|--|
| What it analyzes | Terraform plan | Terraform files | Terraform files | Terraform plan |
| Detection method | Deterministic rules | Policy-as-code | Policy-as-code | Pricing API |
| Blast radius | Yes (v1.1) | No | No | No |
| CI exit codes | Yes | Yes | Yes | No |
| Cost estimation | No (v2 via Infracost) | No | No | Yes |
| Reads live AWS | No (v1) | No | No | No |
| Language | Python | Python | Go | Go |

IACGuard is not trying to replace Checkov or tfsec — it runs alongside them. The differentiator is blast radius analysis: understanding what downstream resources are affected by each planned change. No other free CLI tool does this in an integrated pre-deploy workflow.

---

## Roadmap

**v0.1.0 — current**
- Terraform plan parser
- 3 deterministic rules (RDS001, SG001, S3001)
- CLI output with color coding
- CI mode with JSON and exit codes

**v0.2.0**
- Blast radius computation from Terraform dependency graph
- Additional rules: RDP (SG002), database ports (SG003), missing tags (TAG001)

**v0.3.0**
- Binary drift detection — Terraform state vs live AWS
- Checkov sidecar output
- Infracost cost delta integration

**v1.0.0**
- Browser-based dependency graph visualization (`--ui` flag)
- Multi-region support
- AI explanation layer (`--explain` flag, Claude API)

---

## Contributing

Rules are the easiest place to contribute. Each rule is a single Python file in `iacguard/rules/` that follows this pattern:

```python
from iacguard.rules.base import RuleBase, ResourceChange, Finding, Severity, Action

class YOURRULE(RuleBase):
    rule_id  = "XY001"
    severity = Severity.HIGH

    def check(self, change: ResourceChange, all_changes: list):
        if change.resource_type != "aws_your_resource":
            return None
        # your detection logic here
        return Finding(
            rule_id=self.rule_id,
            severity=self.severity,
            resource_address=change.address,
            resource_type=change.resource_type,
            resource_name=change.name,
            action=change.action,
            message="What went wrong",
            recommendation="How to fix it",
        )
```

Add the rule to `iacguard/engine/runner.py` and add a test fixture and test file. Open a pull request.

---

## License

MIT

---

## Author

Built by [adil-khan-723](https://github.com/adil-khan-723)
