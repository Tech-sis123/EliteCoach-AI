package com.elitecoach.notification_service.event;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NotificationEvent {
    private String event;
    private String learner_id;
    private String course_id;
    private String session_id;
    private Map<String, Object> additionalData;
}