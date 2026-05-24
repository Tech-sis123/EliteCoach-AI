from sqlalchemy.ext.asyncio import AsyncSession
from app.models.analytics import Event
from app.core.logging import logger
import uuid
import asyncio

class AnalyticsService:
    async def track(self, event_type: str, actor_id: uuid.UUID = None, entity_type: str = None, entity_id: uuid.UUID = None, metadata: dict = None):
        # Fire and forget pattern
        asyncio.create_task(self._record_event(event_type, actor_id, entity_type, entity_id, metadata))

    async def _record_event(self, event_type, actor_id, entity_type, entity_id, metadata):
        from app.core.database import AsyncSessionLocal
        try:
            async with AsyncSessionLocal() as db:
                event = Event(
                    event_type=event_type,
                    actor_id=actor_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    payload=metadata
                )
                db.add(event)
                await db.commit()
        except Exception as e:
            logger.error("analytics_track_failed", error=str(e), event_type=event_type)

analytics_service = AnalyticsService()
