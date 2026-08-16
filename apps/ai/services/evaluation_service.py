import math
from typing import List, Dict

class EvaluationService:
    """Computes regression evaluation metrics (R^2, RMSE, MAE, MAPE)."""

    @staticmethod
    def evaluate_regression(y_true: List[float], y_pred: List[float]) -> Dict[str, float]:
        """Calculates R^2, RMSE, MAE, and MAPE between true and predicted arrays."""
        n = len(y_true)
        if n == 0 or len(y_pred) != n:
            return {'r2': 0.0, 'rmse': 0.0, 'mae': 0.0, 'mape': 0.0}

        mean_y = sum(y_true) / n
        ss_tot = sum((y - mean_y) ** 2 for y in y_true)
        ss_res = sum((y_t - y_p) ** 2 for y_t, y_p in zip(y_true, y_pred))

        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        mse = ss_res / n
        rmse = math.sqrt(mse)
        mae = sum(abs(y_t - y_p) for y_t, y_p in zip(y_true, y_pred)) / n
        
        # MAPE with zero-division guard
        mape_vals = [abs((y_t - y_p) / y_t) for y_t, y_p in zip(y_true, y_pred) if y_t != 0]
        mape = (sum(mape_vals) / len(mape_vals) * 100.0) if mape_vals else 0.0

        return {
            'r2': round(max(-1.0, min(1.0, r2)), 4),
            'rmse': round(rmse, 4),
            'mae': round(mae, 4),
            'mape': round(mape, 2)
        }
