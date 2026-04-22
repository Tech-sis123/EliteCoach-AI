package org.identity_service.EliteCoach.controller;

import jakarta.servlet.http.HttpServletRequest;
import org.identity_service.EliteCoach.dto.UserRequest;
import org.identity_service.EliteCoach.model.User;
import org.identity_service.EliteCoach.service.JwtService;
import org.identity_service.EliteCoach.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @Autowired
    private JwtService jwtService;
    @Autowired
    private UserService userService;

    @GetMapping("/profile")
    public ResponseEntity<UserRequest> getUserProfile(HttpServletRequest servletRequest) {
        return ResponseEntity.ok().body(userService.getUserProfile(fetchPrincipalEmail(servletRequest)));
    }

    public String fetchPrincipalEmail(HttpServletRequest servletRequest) {
        String header = servletRequest.getHeader("Authorization");
        String email = null;
        if(header != null) {
            String token = header.substring(7);
            email = jwtService.extractEmail(token);
        }
        return email;
    }
}
