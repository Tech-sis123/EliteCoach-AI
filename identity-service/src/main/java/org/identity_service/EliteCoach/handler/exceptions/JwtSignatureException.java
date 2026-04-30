package org.identity_service.EliteCoach.handler.exceptions;

public class JwtSignatureException extends RuntimeException {
    public JwtSignatureException(String message) {
        super(message);
    }
}
