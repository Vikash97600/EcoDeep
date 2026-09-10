from apps.experiments.models import ScientificDataset


class ReportGeneratorService:
    """Generates publication-ready research summaries and LaTeX empirical tables."""

    @staticmethod
    def generate_latex_table(dataset: ScientificDataset) -> str:
        """Generates an IEEE/ACM compliant LaTeX descriptive statistics table."""
        stats = dataset.statistics.filter(metric_name='execution_time_ms')
        
        latex = [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{Empirical Benchmark Performance & Energy Comparison: " + dataset.dataset_name + r"}",
            r"\label{tab:benchmark_results}",
            r"\begin{tabular}{lcccccc}",
            r"\hline",
            r"\textbf{Library} & \textbf{N} & \textbf{Mean (ms)} & \textbf{Std Dev} & \textbf{Median} & \textbf{95\% CI} & \textbf{CV (\%)} \\",
            r"\hline"
        ]

        for s in stats:
            ci_str = f"[{s.ci_95_lower:.2f}, {s.ci_95_upper:.2f}]"
            row = f"{s.library.library_name} & {s.sample_size} & {s.mean:.2f} & {s.std_dev:.2f} & {s.median:.2f} & {ci_str} & {s.coefficient_of_variation:.1f}\\% \\\\"
            latex.append(row)

        latex.extend([
            r"\hline",
            r"\end{tabular}",
            r"\end{table}"
        ])

        return "\n".join(latex)

    @staticmethod
    def generate_markdown_report(dataset: ScientificDataset) -> str:
        """Generates a complete research summary in Markdown."""
        exp = dataset.experiment
        md = [
            f"# Empirical Research Report: {exp.title}",
            f"**Dataset:** {dataset.dataset_name} (v{dataset.semantic_version})  ",
            f"**Confidence Index:** {dataset.confidence_index:.1f}% | **Data Quality:** {dataset.data_quality_score:.1f}%  ",
            f"**Checksum:** `{dataset.checksum_sha256}`  \n",
            "## 1. Research Question & Hypotheses",
            f"- **Question:** {exp.research_question}",
            f"- **H0 (Null):** {exp.null_hypothesis}",
            f"- **H1 (Alternative):** {exp.alternative_hypothesis}\n",
            "## 2. Experimental Setup",
            f"- **Warm-up Runs:** {exp.warmup_iterations} (discarded)",
            f"- **Measurement Repetitions:** {exp.measurement_iterations}",
            f"- **Outlier Detection Method:** {exp.get_outlier_method_display()}",
            f"- **Total Outliers Detected:** {dataset.total_outliers}\n",
            "## 3. Descriptive Statistics Summary",
            "| Library | Metric | Mean | Std Dev | Median | 95% Confidence Interval | CV (%) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        for s in dataset.statistics.all():
            ci_str = f"[{s.ci_95_lower:.2f}, {s.ci_95_upper:.2f}]"
            md.append(f"| **{s.library.library_name}** | {s.metric_name} | {s.mean:.3f} | {s.std_dev:.3f} | {s.median:.3f} | {ci_str} | {s.coefficient_of_variation:.1f}% |")

        md.append("\n## 4. Hypothesis Testing Results")
        for test in dataset.hypothesis_tests.all():
            md.append(f"- **{test.baseline_library.library_name} vs {test.target_library.library_name} ({test.metric_name}):**")
            md.append(f"  - *p-value:* `{test.p_value:.6f}` (alpha=0.05)")
            md.append(f"  - *Effect Size ({test.effect_size_name}):* `{test.effect_size_value:.2f}` ({test.effect_size_magnitude})")
            md.append(f"  - *Decision:* {'Reject H0 (Statistically Significant)' if test.reject_null_hypothesis else 'Fail to Reject H0'}")
            md.append(f"  - *Interpretation:* {test.interpretation}")

        return "\n".join(md)
