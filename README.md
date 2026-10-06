# Freight Operations Assistant

Review the pilot and proposed design for fifty customers.

- [Assignment](ASSIGNMENT.md)
- [Report](report.md): findings, architecture, and cost projections.
- [Reflection](reflection.md): uncertain decisions and AI errors.
- [Costs and limits](costs-and-limits.md)

Files: `scripts/` contains analysis code and checks; [poc/](poc/README.md)
contains example application code; [data/](data/README.md) contains inputs;
`docs/architecture/` contains diagrams, design notes, and cost inputs.
Results remain in [pilot_outputs/](pilot_outputs/results.md),
[model_outputs/](model_outputs/results.md), `model_outputs_half_lead/`,
and `redesign_cost_outputs/`.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
Run from the repository root:

```powershell
uv sync --locked
uv run --locked scripts/test_pilot_analysis.py
uv run --locked scripts/analyze_pilot.py
uv run --locked scripts/cost_model.py
uv run --locked scripts/plot_costs.py
uv run --locked scripts/plot_redesign_costs.py
```

For half the lead question frequency, run
`uv run --locked scripts/cost_model.py --lead-frequency 0.5 --output model_outputs_half_lead`.
Pilot analysis, the cost model, and the original cost charts accept `--data`
and `--output`. Each run replaces its output files.

The POC is for review, not execution. Answer accuracy and proposed savings
are unmeasured. Cost projections exclude infrastructure.
