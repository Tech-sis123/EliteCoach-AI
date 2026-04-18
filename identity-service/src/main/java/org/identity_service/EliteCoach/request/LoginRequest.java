package org.identity_service.EliteCoach.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotNull;

public record LoginRequest(@Email String email, @NotNull(message = "Password cannot be null") String password) {
}
