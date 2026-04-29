package org.identity_service.EliteCoach.dto;


import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import org.identity_service.EliteCoach.model.UserStatus;
import org.identity_service.EliteCoach.model.UserType;

import java.util.UUID;

@Data
public class UserRequest {

    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    private UUID userId;
    @NotNull(message = "First name cannot be null")
    private String firstName;

    @NotNull(message = "Last name cannot be null")
    private String lastName;
    @NotNull(message = "Password cannot be null")
    @JsonProperty(access = JsonProperty.Access.WRITE_ONLY)
    private String password;
    @Email
    private String email;
    private UserType userType;

}
