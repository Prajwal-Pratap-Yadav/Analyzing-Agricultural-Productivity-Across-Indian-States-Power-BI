# Agricultural data quality audit: review guide

Trace how an agricultural reporting project handles inconsistent arithmetic and uncertain source semantics before presenting results.

## Follow the implementation

| Start here | File | What to inspect |
| --- | --- | --- |
| Explicit policy | [src/etl/policy.py](../src/etl/policy.py) | Rules for accepting, flagging, or excluding records. |
| Validation | [src/etl/validate.py](../src/etl/validate.py) | Checks that turn source uncertainty into visible findings. |
| ETL tests | [tests/test_etl.py](../tests/test_etl.py) | Transformation and reconciliation contracts. |
| Original preservation | [tests/test_original.py](../tests/test_original.py) | Protection for archived source material. |
| Validation report | [reports/validation_report.json](../reports/validation_report.json) | The recorded row-level audit outcome. |
| Data documentation | [docs/DATA.md](../docs/DATA.md) | Units, geography, provenance, and interpretation boundaries. |

## Run the checks

Run from the repository root after the setup described in the [README](../README.md). Review fixtures and recorded evidence before starting any full experiment.

```bash
make setup-dev
make test docs
make reproduce
```

## Interpret the evidence

Arithmetic disagreement is evidence of a data-quality problem, not proof that a particular crop or state performed badly. Uncertain units and geography limit direct productivity comparisons. The Python companion and archived Power BI artifact have separate evidence boundaries.

The linked reports retain their original experiment dates and protocols. A new passing CI run verifies its named checks; it does not silently refresh historical measurements.

## Discuss the design

- Why flag questionable records rather than silently repair them?
- How should a dashboard communicate an uncertain denominator?
