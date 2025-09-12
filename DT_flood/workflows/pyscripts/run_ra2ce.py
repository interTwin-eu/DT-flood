"""Script to run ra2ce model, run in docker."""

from pathlib import Path

from ra2ce.ra2ce_handler import Ra2ceHandler  # type: ignore

root = Path("data")

analysis_ini = root / "analysis.ini"
network_ini = root / "network.ini"

handler = Ra2ceHandler(network=network_ini, analysis=analysis_ini)
handler.configure()
handler.run_analysis()
