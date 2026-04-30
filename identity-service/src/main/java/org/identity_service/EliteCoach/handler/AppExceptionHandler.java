package org.identity_service.EliteCoach.handler;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.identity_service.EliteCoach.handler.exceptions.JwtSignatureException;
import org.identity_service.EliteCoach.handler.exceptions.UserNotFoundException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class AppExceptionHandler {

    public Map<String, Object> handleCustomMailException(Exception ex, String error, HttpServletRequest request, HttpServletResponse servletResponse) {
        Map<String, Object> response = new HashMap<>();
        response.put("error", error);
        response.put("path", request.getRequestURI());
        response.put("status", servletResponse.getStatus());
        response.put("message", ex.getMessage());
        return response;
    }

    @ExceptionHandler(UserNotFoundException.class)
    public Map<String, Object> handleUserNotFoundException(UserNotFoundException userNotFoundException, HttpServletRequest request, HttpServletResponse servletResponse) {
        return handleCustomMailException(userNotFoundException, "User details not found", request, servletResponse);
    }
    @ExceptionHandler(io.jsonwebtoken.security.SignatureException.class)
    public Map<String, Object> handleUserNotFoundException(io.jsonwebtoken.security.SignatureException jwtSignatureException, HttpServletRequest request, HttpServletResponse servletResponse) {
        return handleCustomMailException(jwtSignatureException, "Invalid Jwt token", request, servletResponse);
    }
}
