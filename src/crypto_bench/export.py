from pathlib import Path
import json
import pandas as pd
from .statistics import descriptive, anova
def write_csv(rows, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
def export_workbook(csv_path, output=None, metadata=None):
    df = pd.read_csv(csv_path)
    output = output or str(Path(csv_path).with_name("summary.xlsx"))
    if metadata is None:
        mpath = Path(csv_path).with_name("metadata.json")
        metadata = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    with pd.ExcelWriter(output, engine="openpyxl") as w:
        pd.DataFrame([metadata]).to_excel(w, "Run Metadata", index=False)
        df.to_excel(w, "Raw Timings", index=False)
        df[[c for c in ["algorithm","baseline_rss_mib","peak_rss_mib","incremental_peak_rss_mib"] if c in df]].to_excel(w, "Memory", index=False)
        df[[c for c in ["algorithm","overhead_bytes","payload_size_bytes"] if c in df]].to_excel(w, "Overhead", index=False)
        descriptive(df).to_excel(w, "Descriptive Stats", index=False)
        anova(df).to_excel(w, "ANOVA", index=False)
        pd.DataFrame().to_excel(w, "Post Hoc", index=False)
    return output
