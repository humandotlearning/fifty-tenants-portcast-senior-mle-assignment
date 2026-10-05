# Run the cost model and charts

## Show the pilot issues

Run these commands from the repository folder:

```powershell
uv run --locked analyze_pilot.py
uv run --locked test_pilot_analysis.py
```

The analysis creates six charts in [pilot_outputs](pilot_outputs/results.md).
The charts show timeouts, shipment checks, Monday carrier limits, spend,
cache scope, and data freshness. Each chart has a PNG preview and an SVG file.
CSV files contain the evidence. The script checks billing and log totals.
Cache source matches are inferred. Answer accuracy is not measured.

Use `--data` and `--output` to select other folders. Each run replaces its output files.

## Run the cost model

The model learns four average question costs. It separates operator and team lead questions. It also separates “my shipments” from other questions. It checks predictions on the final two weeks. It compares these predictions with averages based only on role. The tenant projection keeps each role's pilot usage pattern. See [the results](model_outputs/results.md) for assumptions.

The cost model uses only the Python standard library. The chart script uses `matplotlib`. The files in `poc/` are examples for review. They are not runnable scripts.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/). Then run these commands from the repository folder:

```powershell
uv sync --locked
uv run --locked cost_model.py
uv run --locked plot_costs.py
```

`uv` selects Python 3.10 from `.python-version`. It creates `.venv` and installs the package versions in `uv.lock`. It downloads Python if needed. You do not need to activate `.venv` or set `PYTHONPATH`. If you previously set `PYTHONPATH` to `.plot_deps`, clear it before you run the scripts.

Outputs go into `model_outputs`:

- `tenant_costs.csv`: each customer's cost, revenue, and margin.
- `fit_heldout.png`: actual question costs as blue dots. Predictions are orange lines. Actual group averages are green diamonds.
- `monthly_spending.png`: operator and lead costs under three assumptions.

To assume leads ask half as many questions, keep their question mix unchanged:

```powershell
uv run --locked cost_model.py --lead-frequency 0.5 --output model_outputs_half_lead
```

Both scripts accept `--data` and `--output`. Use these options to select other folders:

```powershell
uv run --locked cost_model.py --data data --output outputs
uv run --locked plot_costs.py --data data --output outputs
```

The chart script always shows both full and half lead frequency. It has no frequency option. Each run replaces the generated files in the selected output folder.

To add a package, run `uv add <package>`. To remove a package, run `uv remove <package>`. Commit `pyproject.toml` and `uv.lock` after you change dependencies.

**$12,523.41/month = 6.47 times** fifty identical pilots ($1,935.31). With half lead frequency, **$6,754.57/month = 3.49 times** that baseline.

These costs include the model and carrier for 30-day months. Calculations use unrounded rates. Rounded chart labels can differ from their total by one cent. The pilot had only one team lead. The charts show costs under stated assumptions. They do not prove a relationship between customer size and spending. They do not prove system capacity.
