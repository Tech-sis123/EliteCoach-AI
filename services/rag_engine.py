import os
import logging
from typing import List, Dict, Optional, Any
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import json

logger = logging.getLogger(__name__)


class RAGTutorEngine:
    """RAG (Retrieval-Augmented Generation) Pipeline for AI Tutor"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.embeddings = None
        self.model = None
        
        # Initialize OpenAI components only if API key is available
        if self.openai_api_key:
            try:
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=self.openai_api_key
                )
                
                self.model = ChatOpenAI(
                    model_name="gpt-4",
                    temperature=0.7,
                    max_tokens=1000,
                    openai_api_key=self.openai_api_key
                )
                logger.info("OpenAI embeddings and model initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI components: {str(e)}")
                self.embeddings = None
                self.model = None
        else:
            logger.warning("OPENAI_API_KEY not set. OpenAI features will be unavailable.")
        
        # Simulated vector store - in production use Pinecone/Weaviate
        self.vector_store: Dict[str, List[Dict]] = {}
    
    async def index_course_content(
        self,
        course_id: str,
        content_chunks: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Index course content into vector store"""
        
        try:
            indexed_chunks = []
            
            for i, chunk in enumerate(content_chunks):
                # Generate embedding for each chunk
                embedding = await self._embed_text(chunk['text'])
                
                chunk_data = {
                    'id': f"{course_id}_chunk_{i}",
                    'course_id': course_id,
                    'text': chunk['text'],
                    'embedding': embedding,
                    'source': chunk.get('source', 'unknown'),
                    'type': chunk.get('type', 'lesson')
                }
                
                indexed_chunks.append(chunk_data)
            
            # Store in vector store
            self.vector_store[course_id] = indexed_chunks
            
            logger.info(f"Indexed {len(indexed_chunks)} chunks for course {course_id}")
            
            return {
                'course_id': course_id,
                'chunks_indexed': len(indexed_chunks),
                'status': 'indexed'
            }
        
        except Exception as e:
            logger.error(f"Error indexing course content: {str(e)}")
            raise
    
    async def generate_response(
        self,
        learner_id: str,
        course_id: str,
        learner_message: str,
        conversation_history: List[Dict[str, str]],
        course_title: str = "Course"
    ) -> Dict[str, Any]:
        """Generate AI tutor response using RAG pipeline"""
        
        try:
            # Step 1: Embed the learner's question
            message_embedding = await self._embed_text(learner_message)
            
            # Step 2: Retrieve relevant content chunks (semantic search)
            relevant_chunks = await self._retrieve_relevant_chunks(
                course_id,
                message_embedding,
                top_k=5
            )
            
            # Step 3: Build system prompt with context
            system_prompt = self._build_system_prompt(
                course_title,
                relevant_chunks
            )
            
            # Step 4: Build conversation messages
            messages = self._build_conversation_messages(
                system_prompt,
                conversation_history,
                learner_message
            )
            
            # Step 5: Generate response from LLM
            if self.model is None:
                logger.warning("OpenAI model not available. Using mock response.")
                response_text = f"I'd be happy to help you with: {learner_message}. Since the AI system is not fully configured, please try again when the service is ready."
                response = type('obj', (object,), {'content': response_text})()
            else:
                response = self.model(messages)
            
            # Step 6: Check for escalation triggers
            escalation_needed = self._check_escalation_triggers(
                learner_message,
                conversation_history,
                relevant_chunks
            )
            
            return {
                'response': response.content,
                'relevant_chunks_count': len(relevant_chunks),
                'average_confidence': self._calculate_avg_confidence(relevant_chunks),
                'escalation_needed': escalation_needed,
                'model_used': 'gpt-4',
                'metadata': {
                    'retrieved_sources': [chunk['source'] for chunk in relevant_chunks],
                    'message_length': len(learner_message)
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return {
                'response': f"I encountered an error. Please try again. Error: {str(e)}",
                'error': True,
                'escalation_needed': True
            }
    
    async def _embed_text(self, text: str) -> List[float]:
        """Convert text to embedding vector"""
        try:
            if self.embeddings is None:
                logger.warning("OpenAI embeddings not available. Using mock embedding.")
                # Return a mock embedding vector (all zeros with same dimension as real embeddings)
                return [0.0] * 1536  # OpenAI embeddings are 1536-dimensional
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error embedding text: {str(e)}")
            # Return mock embedding on error
            return [0.0] * 1536
    
    async def _retrieve_relevant_chunks(
        self,
        course_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant content chunks using semantic similarity"""
        
        if course_id not in self.vector_store:
            logger.warning(f"No indexed content for course {course_id}")
            return []
        
        chunks = self.vector_store[course_id]
        
        # Calculate similarity scores
        scored_chunks = []
        for chunk in chunks:
            similarity = self._cosine_similarity(query_embedding, chunk['embedding'])
            scored_chunks.append({
                **chunk,
                'similarity_score': similarity
            })
        
        # Sort by similarity and return top-k
        top_chunks = sorted(
            scored_chunks,
            key=lambda x: x['similarity_score'],
            reverse=True
        )[:top_k]
        
        return top_chunks
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        
        if not vec1 or not vec2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a ** 2 for a in vec1))
        mag2 = math.sqrt(sum(b ** 2 for b in vec2))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def _build_system_prompt(
        self,
        course_title: str,
        relevant_chunks: List[Dict[str, Any]]
    ) -> str:
        """Build system prompt with course context"""
        
        context = "\n".join([
            f"- {chunk['text']} (confidence: {chunk['similarity_score']:.1%})"
            for chunk in relevant_chunks
        ])
        
        system_prompt = f"""You are Elite Coach AI, an expert tutor specializing in {course_title}.

Your responsibilities:
- Answer questions ONLY based on the provided course content below
- Give clear, concise, professional-level explanations
- Provide practical examples when relevant
- Encourage critical thinking and deeper understanding
- If you don't know the answer from the course content, say "I don't have that information in this course"
- If learner asks the same question 3+ times or seems frustrated, suggest escalation to a human tutor

Course Content:
{context}

Remember: You are helping professionals master skills. Be supportive, encourage questions, and maintain high standards."""
        
        return system_prompt
    
    def _build_conversation_messages(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        current_message: str
    ) -> List:
        """Build conversation message list for LLM"""
        
        messages = [SystemMessage(content=system_prompt)]
        
        # Add last 5 messages for context (avoid token limits)
        for msg in conversation_history[-5:]:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                messages.append(AIMessage(content=msg['content']))
        
        # Add current message
        messages.append(HumanMessage(content=current_message))
        
        return messages
    
    def _check_escalation_triggers(
        self,
        current_message: str,
        history: List[Dict[str, str]],
        retrieved_chunks: List[Dict[str, Any]]
    ) -> bool:
        """Check if session should be escalated to human tutor"""
        
        # Trigger 1: Low average confidence in retrieved chunks
        if retrieved_chunks:
            avg_confidence = sum(c['similarity_score'] for c in retrieved_chunks) / len(retrieved_chunks)
            if avg_confidence < 0.3:
                logger.info(f"Low confidence escalation trigger: {avg_confidence:.2f}")
                return True
        
        # Trigger 2: Repeated questions (same question asked 3+ times)
        similar_questions = sum(
            1 for msg in history[-10:]
            if msg['role'] == 'user' and self._message_similarity(msg['content'], current_message) > 0.8
        )
        if similar_questions >= 3:
            logger.info("Repeated question escalation trigger")
            return True
        
        # Trigger 3: Frustration indicators
        frustration_keywords = ['confused', 'don\'t understand', 'not helping', 'frustrated', 'stuck']
        if any(keyword in current_message.lower() for keyword in frustration_keywords):
            logger.info("Frustration keyword detected")
            return True
        
        # Trigger 4: Explicit help request
        if any(phrase in current_message.lower() for phrase in ['help me', 'talk to tutor', 'human tutor']):
            logger.info("Explicit help request")
            return True
        
        return False
    
    def _message_similarity(self, msg1: str, msg2: str) -> float:
        """Calculate Jaccard similarity between two messages"""
        
        words1 = set(msg1.lower().split())
        words2 = set(msg2.lower().split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _calculate_avg_confidence(self, chunks: List[Dict[str, Any]]) -> float:
        """Calculate average confidence score"""
        
        if not chunks:
            return 0.0
        
        return sum(c['similarity_score'] for c in chunks) / len(chunks)


# Singleton instance
rag_engine = RAGTutorEngine()
