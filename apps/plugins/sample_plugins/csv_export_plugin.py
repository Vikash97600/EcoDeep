import csv
import io
from typing import Any

from apps.plugins.sdk.interfaces import ExportPlugin
from apps.plugins.sdk.manifest import PluginMetadata


class CSVExportPlugin(ExportPlugin):
    """Reference implementation of a CSV data exporter plugin."""

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="ecodep.exporter.csv",
            name="CSV Telemetry Exporter Plugin",
            version="1.0.0",
            author="EcoDep Core Team",
            category="EXPORT_GENERATOR",
            description="Exports research telemetry datasets into standardized CSV files",
            entry_class="apps.plugins.sample_plugins.csv_export_plugin.CSVExportPlugin"
        )

    def export_data(self, dataset: list[dict[str, Any]]) -> bytes:
        output = io.StringIO()
        if not dataset:
            return output.getvalue().encode('utf-8')

        writer = csv.DictWriter(output, fieldnames=dataset[0].keys())
        writer.writeheader()
        writer.writerows(dataset)
        return output.getvalue().encode('utf-8')
