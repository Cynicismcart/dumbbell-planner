from dataclasses import dataclass
from typing import List, Dict

@dataclass
class PlateType:
    weight: float        # kg per plate
    thickness: float     # cm per plate
    count: int           # total plates available
    label: str = ""      # optional display label

    def display(self) -> str:
        return self.label or f"{self.weight:g} kg"

@dataclass
class ComboResult:
    total_weight: float              # kg (plates only; total for implement = 2*side_weight)
    per_side_thickness: float        # cm
    per_side_counts: Dict[int, int]  # key=index in original plate list
    note: str = ""

def _round(x: float, nd=3) -> float:
    return round(x + 1e-12, nd)

def _make_note(plates: List[PlateType], counts: Dict[int, int]) -> str:
    parts = []
    order = sorted(counts.items(), key=lambda kv: (-plates[kv[0]].weight, -plates[kv[0]].thickness))
    for idx, n in order:
        if n > 0:
            parts.append(f"{plates[idx].display()}×{n}")
    return " + ".join(parts) if parts else "（空）"

def enumerate_symmetric_combos(
    plates: List[PlateType],
    side_len_cm: float,
    mode: str = "pair",   # "pair" (×4 inventory), "connector" (×2), "single" (×2)
    include_zero: bool = False,
) -> List[ComboResult]:
    assert mode in ("pair", "connector", "single"), "mode must be 'pair', 'connector', or 'single'"
    factor = 4 if mode == "pair" else 2  # 'connector' and 'single' both use factor 2

    # Per-side caps under inventory
    per_side_caps = [p.count // factor for p in plates]
    usable_idx = [i for i, cap in enumerate(per_side_caps) if cap > 0]
    if not usable_idx and not include_zero:
        return []

    f_plates = [plates[i] for i in usable_idx]
    f_caps   = [per_side_caps[i] for i in usable_idx]

    # order by thickness desc for pruning
    order = sorted(range(len(f_plates)), key=lambda i: -f_plates[i].thickness)
    f_plates = [f_plates[i] for i in order]
    f_caps   = [f_caps[i] for i in order]
    idx_map  = {i: usable_idx[order[i]] for i in range(len(order))}

    results: List[ComboResult] = []

    def dfs(i: int, used_thick: float, side_weight: float, counts: List[int]):
        if used_thick - 1e-9 > side_len_cm:
            return
        if i == len(f_plates):
            if include_zero or side_weight > 0:
                per_side_counts = {idx_map[j]: counts[j] for j in range(len(counts)) if counts[j] > 0}
                total = side_weight * 2.0
                results.append(ComboResult(
                    total_weight=_round(total, 3),
                    per_side_thickness=_round(used_thick, 3),
                    per_side_counts=per_side_counts,
                    note=_make_note(plates, per_side_counts)
                ))
            return
        p = f_plates[i]
        max_by_len = int((side_len_cm - used_thick + 1e-9) // p.thickness)
        hi = min(f_caps[i], max_by_len)
        for n in range(hi, -1, -1):
            counts.append(n)
            dfs(i + 1, used_thick + n * p.thickness, side_weight + n * p.weight, counts)
            counts.pop()

    dfs(0, 0.0, 0.0, [])

    # Dedup
    seen = set()
    out: List[ComboResult] = []
    for r in results:
        key = (r.total_weight, r.per_side_thickness, tuple(sorted(r.per_side_counts.items())))
        if key not in seen:
            seen.add(key)
            out.append(r)
    out.sort(key=lambda r: (-r.total_weight, r.per_side_thickness))
    return out
