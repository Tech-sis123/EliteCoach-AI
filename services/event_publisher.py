import aio_pika
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from core.config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes domain events to RabbitMQ for async processing"""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self.is_connected = False
    
    async def connect(self, rabbitmq_url: str = None):
        """Establish connection to RabbitMQ"""
        url = rabbitmq_url or settings.RABBITMQ_URL
        try:
            self.connection = await aio_pika.connect_robust(url)
            self.channel = await self.connection.channel()
            
            # Declare exchange for events
            self.exchange = await self.channel.declare_exchange(
                name="elite-coach-events",
                type=aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            self.is_connected = True
            logger.info("Connected to RabbitMQ")
        
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise
    
    async def disconnect(self):
        """Close connection to RabbitMQ"""
        if self.connection:
            await self.connection.close()
            self.is_connected = False
            logger.info("Disconnected from RabbitMQ")
    
    async def publish_learner_session_started(
        self,
        learner_id: str,
        course_id: str,
        session_id: str,
        module_id: Optional[str] = None
    ) -> bool:
        """Publish event when learner starts a session"""
        
        event = {
            'event': 'LEARNER_SESSION_STARTED',
            'learner_id': learner_id,
            'course_id': course_id,
            'session_id': session_id,
            'module_id': module_id,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'learning-service'
        }
        
        return await self._publish_event('learner.session.started', event)
    
    async def publish_learner_session_completed(
        self,
        learner_id: str,
        course_id: str,
        session_id: str,
        duration_minutes: int,
        topics_learned: list,
        escalated: bool = False
    ) -> bool:
        """Publish event when learner completes a session"""
        
        event = {
            'event': 'LEARNER_SESSION_COMPLETED',
            'learner_id': learner_id,
            'course_id': course_id,
            'session_id': session_id,
            'duration_minutes': duration_minutes,
            'topics_learned': topics_learned,
            'escalated': escalated,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'learning-service'
        }
        
        return await self._publish_event('learner.session.completed', event)
    
    async def publish_learner_course_completed(
        self,
        learner_id: str,
        course_id: str,
        score: float,
        time_taken_hours: float
    ) -> bool:
        """Publish event when learner completes a course"""
        
        event = {
            'event': 'LEARNER_COURSE_COMPLETED',
            'learner_id': learner_id,
            'course_id': course_id,
            'score': score,
            'time_taken_hours': time_taken_hours,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'learning-service'
        }
        
        return await self._publish_event('learner.course.completed', event)
    
    async def publish_escalation_triggered(
        self,
        learner_id: str,
        session_id: str,
        course_id: str,
        reason: str
    ) -> bool:
        """Publish event when session needs escalation"""
        
        event = {
            'event': 'ESCALATION_TRIGGERED',
            'learner_id': learner_id,
            'session_id': session_id,
            'course_id': course_id,
            'escalation_reason': reason,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'learning-service'
        }
        
        return await self._publish_event('escalation.triggered', event)
    
    async def publish_ai_response_generated(
        self,
        learner_id: str,
        session_id: str,
        course_id: str,
        model_used: str,
        tokens_used: int,
        confidence_score: float
    ) -> bool:
        """Publish event for analytics when AI generates response"""
        
        event = {
            'event': 'AI_RESPONSE_GENERATED',
            'learner_id': learner_id,
            'session_id': session_id,
            'course_id': course_id,
            'model_used': model_used,
            'tokens_used': tokens_used,
            'confidence_score': confidence_score,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'learning-service'
        }
        
        return await self._publish_event('ai.response.generated', event)
    
    async def _publish_event(self, routing_key: str, event: Dict[str, Any]) -> bool:
        """Internal method to publish event to exchange"""
        
        if not self.is_connected or not self.exchange:
            logger.error("Not connected to RabbitMQ")
            return False
        
        try:
            message = aio_pika.Message(
                body=json.dumps(event).encode(),
                content_type='application/json',
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            await self.exchange.publish(message, routing_key=routing_key)
            
            logger.info(f"Published event: {routing_key} | Event: {event['event']}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}")
            return False


# Singleton instance
event_publisher = EventPublisher()
