package com.elitecoach.notification_service.response;

import lombok.Data;

import java.util.List;

@Data
public class WhatsappNotificationResponse {
    private boolean success;
    private String code;
    private String message;
    private List<NotificationMessage> data;
}
