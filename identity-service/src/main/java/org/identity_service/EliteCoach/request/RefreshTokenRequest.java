package org.identity_service.EliteCoach.request;

import jakarta.validation.constraints.NotNull;

public record RefreshTokenRequest(@NotNull(message="Refresh token cannot be null") String refreshToken) {
}
