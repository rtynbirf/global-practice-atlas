#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Совет 7: тренд-обход по расписанию.
Сиды (data/trend_seeds.json — имена трендов от любого обхода мира) проходят
R5-фильтр: нормализованное пересечение токенов + подстроки против каталога.
Вердикт: покрыт точно / покрыт семейством / КАНДИДАТ-НОВОЕ. Дифф пишется в
data/trend_sweep_report.json. Слияние/паспорта — только решение хозяина."""
import json, re, sys
from collections import OrderedDict

def norm(s):
    return set(re.findall(r"[a-zа-яё0-9]{3,}", (s or "").lower()))

D = json.load(open("data/passports.json", encoding="utf-8"))
live = [p for p in D["passports"] if not str(p.get("status", "")).startswith("поглощён")]
catalog = {p["name_en"].lower(): norm(p["name_en"]) | norm(p.get("name_ru", "")) | norm(str(p.get("description", ""))[:400]) for p in live}
catalog_tok = list(catalog.values())

try:
    seeds = json.load(open("data/trend_seeds.json", encoding="utf-8"))["seeds"]
except FileNotFoundError:
    print("нет data/trend_seeds.json — обходу нужен список имён трендов"); sys.exit(1)

rows = []
for s in seeds:
    name = s.get("name", "").strip()
    cn = norm(name)
    best, j_best, sub = "", 0.0, ""
    for nm, t in catalog.items():
        j = len(cn & t) / max(len(cn | t), 1)
        if j > j_best:
            best, j_best = nm, j
    if j_best >= 0.45:
        verdict, detail = "покрыт точно", f"≈ {best} (Jaccard {j_best:.2f})"
    elif j_best >= 0.25 or any(w in best for w in cn):
        verdict, detail = "покрыт семейством", f"≈ {best} (Jaccard {j_best:.2f})"
    else:
        verdict, detail = "КАНДИДАТ-НОВОЕ", "по каталогу не найдено — паспорт по R5 только по решению хозяина"
    rows.append(OrderedDict(name=name, source=s.get("source", ""), verdict=verdict, detail=detail))
    print(f"  [{verdict:16}] {name[:44]:44} | {detail}")

new = [r for r in rows if r["verdict"] == "КАНДИДАТ-НОВОЕ"]
rep = {"date": None, "seeds": len(seeds), "covered_exact": sum(1 for r in rows if r["verdict"] == "покрыт точно"),
       "covered_family": sum(1 for r in rows if r["verdict"] == "покрыт семейством"),
       "candidates": new, "rows": rows,
       "note": "автослияние запрещено: кандидаты — только сигнал (правило хозяина)"}
json.dump(rep, open("data/trend_sweep_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"ОБХОД: сидов {len(seeds)} · точно {rep['covered_exact']} · семейством {rep['covered_family']} · кандидатов {len(new)} → data/trend_sweep_report.json")
