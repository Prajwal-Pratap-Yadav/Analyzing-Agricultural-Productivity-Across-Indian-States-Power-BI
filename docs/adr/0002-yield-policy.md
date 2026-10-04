# ADR 0002: Preserve reported yield and separate diagnostic arithmetic

Status: accepted, 2026-10-04.

The source does not explain reported yield weighting or per-crop units. Do not overwrite Yield, convert all production to tonnes, rank states across mixed crops, or drop discrepancies as proven errors. Preserve source decimals, compute a separately named production/area ratio and use an explicit symmetric tolerance in Decimal arithmetic. Export all observations plus complete disjoint pass/mismatch slices. Alternatives: silently recompute Yield; sum all crop production; accept all inline dashboard labels as verified semantics. Trade-off: internal consistency flags are useful review evidence, not certified agronomic correctness. Exact relative-boundary cases differ from binary-float reconnaissance and are documented/tested.
