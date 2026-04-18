package org.identity_service.EliteCoach.request;

import lombok.Data;

@Data
public class PasswordResetRequest {

    private String email;
    private String oldPassword;
    private String newPassword;
}
