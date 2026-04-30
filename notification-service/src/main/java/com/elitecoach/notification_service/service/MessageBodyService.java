package com.elitecoach.notification_service.service;

import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class MessageBodyService {

    public String buildSessionStartedEmail(Map<String, Object> event) {
        return """
        📘 Learner Session Started
        
        Learner ID: %s
        Course ID: %s
        Session ID: %s
        Module ID: %s
        Time: %s
        """.formatted(
                event.get("learner_id"),
                event.get("course_id"),
                event.get("session_id"),
                event.get("module_id"),
                event.get("timestamp")
        );
    }

    public String buildSessionCompletedEmail(Map<String, Object> event) {
        return """
        ✅ Session Completed
        
        Learner ID: %s
        Course ID: %s
        Duration: %s minutes
        Topics: %s
        Escalated: %s
        Time: %s
        """.formatted(
                event.get("learner_id"),
                event.get("course_id"),
                event.get("duration_minutes"),
                event.get("topics_learned"),
                event.get("escalated"),
                event.get("timestamp")
        );
    }

    public String buildCourseCompletedEmail(Map<String, Object> event) {
        return """
        🎓 Course Completed
        
        Learner ID: %s
        Course ID: %s
        Score: %s
        Time Taken: %s hours
        Time: %s
        """.formatted(
                event.get("learner_id"),
                event.get("course_id"),
                event.get("score"),
                event.get("time_taken_hours"),
                event.get("timestamp")
        );
    }

    public String buildEscalationEmail(Map<String, Object> event) {
        return """
        🚨 Escalation Triggered
        
        Learner ID: %s
        Session ID: %s
        Course ID: %s
        Reason: %s
        Time: %s
        """.formatted(
                event.get("learner_id"),
                event.get("session_id"),
                event.get("course_id"),
                event.get("escalation_reason"),
                event.get("timestamp")
        );
    }

    public String buildAIResponseEmail(Map<String, Object> event) {
        return """
        🤖 AI Response Generated
        
        Learner ID: %s
        Session ID: %s
        Course ID: %s
        Model: %s
        Tokens Used: %s
        Confidence: %s
        Time: %s
        """.formatted(
                event.get("learner_id"),
                event.get("session_id"),
                event.get("course_id"),
                event.get("model_used"),
                event.get("tokens_used"),
                event.get("confidence_score"),
                event.get("timestamp")
        );
    }
}