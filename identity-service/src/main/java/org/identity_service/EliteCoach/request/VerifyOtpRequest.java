package org.identity_service.EliteCoach.request;

import lombok.Data;

@Data
public class VerifyOtpRequest {

    private String email;
    private String otp;
}
