package com.elitecoach.notification_service.handler;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class AppExceptionHandler {

    public Map<String, Object> handleCustomMailException(CustomMailException ex, String error, HttpServletRequest request, HttpServletResponse servletResponse) {
        Map<String, Object> response = new HashMap<>();
        response.put("error", error);
        response.put("path", request.getRequestURI());
        response.put("status", servletResponse.getStatus());
        response.put("message", ex.getMessage());
        return response;
    }


    @ExceptionHandler(CustomMailException.class)
    public Map<String, Object> handleMailException(CustomMailException mailException, HttpServletRequest request, HttpServletResponse servletResponse) {
        return handleCustomMailException(mailException, "Failed to send email", request, servletResponse);
    }
}
