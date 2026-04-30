package org.identity_service.EliteCoach.request;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

@Data
@AllArgsConstructor
@Builder
public class EmailRequest {

    private String to;
    private String subject;
    private String body;
}
