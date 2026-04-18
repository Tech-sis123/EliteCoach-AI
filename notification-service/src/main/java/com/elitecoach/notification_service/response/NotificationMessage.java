package com.elitecoach.notification_service.response;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class NotificationMessage {

    private String message;
    private String messageId;
    private LocalDateTime timestamp;
}
