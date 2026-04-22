package org.identity_service.EliteCoach.dto;


import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import org.identity_service.EliteCoach.model.UserStatus;
import org.identity_service.EliteCoach.model.UserType;

import java.util.UUID;

@Data
public class UserRequest {

    @NotNull(message = "First name cannot be null")
    private String firstName;

    @NotNull(message = "Last name cannot be null")
    private String lastName;
    @NotNull(message = "Password cannot be null")
    private String password;
    @Email
    private String email;
    private UserType userType;

}
