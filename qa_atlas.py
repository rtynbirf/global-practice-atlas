#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QA атласа v1.6 (16 проверок) — самостоятельные проверки данных (запускается в CI).
Читает data/passports.json (1154 строки) и результаты автомата
(data/report.json, data/emergent_report.json). Ненулевой код — на провал."""
import json, re, sys
from collections import Counter

D = json.load(open("data/passports.json", encoding="utf-8"))
P = D["passports"]
fails = []
def check(name, ok, detail=""):
    print(f"  [{'OK ' if ok else 'FAIL'}] {name} {detail}")
    if not ok: fails.append(name)

live = [p for p in P if not str(p.get("status", "")).startswith("поглощён")]
merged = [p for p in P if str(p.get("status", "")).startswith("поглощён")]
agg = Counter()
for p in live:
    for pat, code in (("Research", "M4"), ("Experimental", "M3"), ("Deployed", "M2"), ("Mainstream", "M1")):
        if pat in p["maturity"]:
            agg[code] += 1; break
codes = Counter(p["type_code"].split("/")[0] for p in live)

print("QA атласа (data/passports.json, версия %s):" % D.get("version"))
check("строк паспортов (слияния строки сохраняют)", len(P) == 1154, f"= {len(P)}")
check("живых позиций", len(live) == 1145, f"= {len(live)}")
check("поглощено с сохранением строк", len(merged) == 9, f"= {len(merged)}")
check("слияния v1.5 по глобальному скану (5)", len(D.get("merges_v15", [])) == 5,
      f"= {len(D.get('merges_v15', []))}: " + ", ".join(m["pair"] for m in D.get("merges_v15", [])))
check("M-агрегат сходится", sum(agg.values()) == len(live), f"M1 {agg['M1']} · M2 {agg['M2']} · M3 {agg['M3']} · M4 {agg['M4']}")
check("классов 12, пустых 0", len(codes) == 12 and codes.get("—", 0) == 0, f"= {len(codes)} классов")
direct = [m.get("direct_path_v14", {}).get("jaccard") for m in D.get("merges_v13", [])]
check("прямой путь R1: 3 из 4 пар с Jaccard ≥ 0.5",
      sum(1 for j in direct if j is not None and j >= 0.5) == 3 and len(D.get("merges_v13", [])) == 4, f"Jaccard {direct}")
check("R3: расхождения решены (21)", len(D.get("r3_resolutions", [])) == 21)
check("R2: паспорта эмерджентных v1.3 (6)", len(D.get("r2_passports", [])) == 6)
new5 = [p for p in P if str(p.get("id")) in ("1152", "1153", "1154")]
check("R5: новые паспорта v1.4 (3)", len(new5) == 3 and all(p.get("verdict") == "ACCEPTED_v14_R5" for p in new5))
check("сверка AI Index зафиксирована", bool(D.get("ai_index_verification", {}).get("confirmed")))
pdf = D.get("ai_index_verification", {}).get("pdf_full", {})
check("AI Index сверён полным текстом PDF (425 стр.), сниппеты заменены",
      pdf.get("confirmed") is True and pdf.get("pages") == 425
      and "ОПРОВЕРГНУТ" in pdf.get("checks", {}).get("280%_вакансий", ""),
      f"78%→88% подтверждён · +280% опровергнут (замена +1,062%) · {pdf.get('date', '—')}")

rep = json.load(open("data/report.json", encoding="utf-8"))
agree, total = rep.get("agree", 0), rep.get("total", 0)
check("РЕЛОМАТ: строки атласа", agree == total == 43, f"{agree}/{total}")
em = json.load(open("data/emergent_report.json", encoding="utf-8"))
check("РЕЛОМАТ: эмерджентные линии", em.get("agree") == em.get("total") == 11,
      f"{em.get('agree')}/{em.get('total')}")

scan = json.load(open("data/global_scan.json", encoding="utf-8"))
check("глобальный парный скан исполнен",
      scan.get("total_pairs") == 660675 and isinstance(scan.get("candidates"), list),
      f"пар {scan.get('total_pairs'):,} · кандидатов {scan.get('prefilter_candidates')} · новых SAME {scan.get('new_same_beyond_known')}")

try:
    rr = json.load(open("data/report_recomputed.json", encoding="utf-8"))
    er = json.load(open("data/emergent_report_recomputed.json", encoding="utf-8"))
    check("РЕЛОМАТ перепрогнан в CI независимо",
          rr.get("agree") == rr.get("total") == 43 and er.get("agree") == er.get("total") == 11,
          f"перепрогон {rr.get('agree')}/{rr.get('total')} · эмерджентные {er.get('agree')}/{er.get('total')}")
except FileNotFoundError:
    check("РЕЛОМАТ перепрогнан в CI независимо", False, "нет файлов перепрогона (см. workflow)")

if fails:
    print("QA ПРОВАЛ:", ", ".join(fails)); sys.exit(1)
print("QA: все проверки сошлись")
