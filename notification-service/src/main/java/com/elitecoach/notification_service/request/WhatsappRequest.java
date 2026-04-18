package com.elitecoach.notification_service.request;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

@Data
@AllArgsConstructor
@Builder
public class WhatsappRequest {

    private String whatsappNumber;
    private String message;
}
