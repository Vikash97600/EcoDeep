from typing import Any


class LaTeXTableService:
    """Converts empirical benchmark results and MCDM Green Scores into publication-ready booktabs LaTeX tables."""

    @staticmethod
    def generate_benchmark_latex_table(candidates: list[dict[str, Any]], caption: str = "Empirical Telemetry & Green Score Comparison", label: str = "tab:benchmark_results") -> str:
        """Generates standardized two-column IEEE / ACM booktabs LaTeX table."""
        latex_lines = [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{" + caption + r"}",
            r"\label{" + label + r"}",
            r"\begin{tabular}{lrrrrr}",
            r"\toprule",
            r"\textbf{Library} & \textbf{Latency (ms)} & \textbf{CPU (\%)} & \textbf{RAM (MB)} & \textbf{Energy (J)} & \textbf{Green Score} \\",
            r"\midrule"
        ]

        for c in candidates:
            lib_name = c.get('library_name', 'Unknown').replace('_', r'\_')
            lat = f"{c.get('execution_time_ms', 0.0):.2f}"
            cpu = rf"{c.get('cpu_utilization_pct', 0.0):.1f}\%"
            ram = f"{c.get('ram_rss_mb', 0.0):.1f}"
            energy = f"{c.get('energy_joules', 0.0):.2f}"
            score = f"{c.get('green_score', 0.0):.1f}"
            latex_lines.append(f"{lib_name} & {lat} & {cpu} & {ram} & {energy} & \\textbf{{{score}}} \\\\")

        latex_lines.extend([
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}"
        ])
        return "\n".join(latex_lines)
