# Run the cost model and charts

The model learns four average question costs: operator or team lead, each split into “my shipments” and other questions. It checks predictions on the final two weeks and compares them with averages based only on role. The tenant projection then keeps each role's pilot usage pattern. See results.md for assumptions.

Model: Python only. Charts: matplotlib. The original 84-line model stays unchanged; plotting is a separate small script.

From the assignment folder:
```powershell
# Already installed here; only needed on a fresh checkout.
python -m pip install --target .plot_deps matplotlib
$env:PYTHONPATH = "$PWD\.plot_deps"
python cost_model.py
python plot_costs.py
```

Outputs go into model_outputs:
- tenant_costs.csv: each customer's cost, revenue and margin.
- fit_heldout.png: actual question costs as blue dots, predictions as orange lines, and actual group averages as green diamonds.
- monthly_spending.png: operator and lead contributions under three assumptions.

To run the saved copies from any directory:
```powershell
$assignment = 'C:\Users\nithi\Downloads\Compressed\fifty-tenants-portcast-senior-mle-assignment\fifty-tenants-portcast-senior-mle-assignment'
$outputs = 'C:\Users\nithi\Documents\Codex\2026-10-04\realtime-voice-chat\outputs\portcast-cost-model'
$env:PYTHONPATH = "$assignment\.plot_deps"
python "$outputs\cost_model.py" --data "$assignment\data" --output "$outputs"
python "$outputs\plot_costs.py" --data "$assignment\data" --output "$outputs"
```

To assume leads ask half as many questions, keeping their question mix unchanged:
```powershell
python "$outputs\cost_model.py" --data "$assignment\data" --lead-frequency 0.5 --output "$outputs\half_lead"
```

The plot script always shows both full and half lead frequency; it has no frequency option. Rerunning replaces its generated PNGs and the model's generated CSV in the selected output folder.

**$12,523.41/month = 6.47 times** fifty identical pilots ($1,935.31). **$6,754.57/month = 3.49 times** that baseline, under half lead frequency. The half case is not the 6.47-times case.

These are model + carrier costs for 30-day months. Calculations retain unrounded rates; displayed component labels may sum one cent differently. Only ONE pilot lead was observed. The charts show conditional cost arithmetic, not a learned relationship between customer size and spending or proof of capacity.
