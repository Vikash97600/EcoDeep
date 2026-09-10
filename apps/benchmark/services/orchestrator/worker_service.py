import socket

import psutil

from apps.benchmark.models import StatusChoices, WorkerHeartbeat, WorkerNode


class WorkerService:
    """Manages worker node registration, heartbeat logging, and lifecycle health checks."""

    @staticmethod
    def register_current_node():
        """Registers local host machine as an active worker node."""
        hostname = socket.gethostname()
        cpu_cores = psutil.cpu_count(logical=True)
        ram_mb = int(psutil.virtual_memory().total / (1024 * 1024))

        node, _ = WorkerNode.objects.update_or_create(
            hostname=hostname,
            defaults={
                'cpu_cores': cpu_cores,
                'ram_mb': ram_mb,
                'status': StatusChoices.ACTIVE,
                'current_load_pct': psutil.cpu_percent()
            }
        )

        # Log heartbeat
        WorkerHeartbeat.objects.create(
            worker=node,
            cpu_percent=node.current_load_pct,
            memory_percent=psutil.virtual_memory().percent
        )

        return node
