from app.worker.tasks import track_event_task
import uuid

class AnalyticsService:
    def track(self, event_type: str, actor_id: uuid.UUID = None, entity_type: str = None, entity_id: uuid.UUID = None, metadata: dict = None):
        # Trigger Celery task
        track_event_task.delay(
            event_type=event_type,
            actor_id=str(actor_id) if actor_id else None,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            metadata=metadata
        )

analytics_service = AnalyticsService()
