package org.identity_service.EliteCoach.request;

import lombok.Data;

import java.util.UUID;

@Data
public class EmailRequest {
    private String to;
    private String subject;
    private String body;
}
