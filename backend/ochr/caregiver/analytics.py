from ochr.context.context_models import UnifiedContext
from .caregiver_models import HealthScore

class AnalyticsEngine:
    def compute_health_score(self, context: UnifiedContext) -> HealthScore:
        return HealthScore(
            overall_score=85,
            bp_trend="Stable",
            sugar_trend="Stable"
        )
