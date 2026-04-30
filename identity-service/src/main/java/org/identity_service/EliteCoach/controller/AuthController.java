package org.identity_service.EliteCoach.controller;

import jakarta.validation.Valid;
import org.identity_service.EliteCoach.dto.UserRequest;
import org.identity_service.EliteCoach.request.*;
import org.identity_service.EliteCoach.service.JwtService;
import org.identity_service.EliteCoach.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    @Autowired
    private UserService userService;
    @Autowired
    private JwtService jwtService;

    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> registerUserAccount(@RequestBody @Valid UserRequest userRequest) {
        return new ResponseEntity<>(userService.createUser(userRequest), HttpStatus.CREATED);
    }

    @PostMapping("/login")
    public void authUser(@RequestBody @Valid LoginRequest loginRequest) {

    }

    @PostMapping("/verify/otp-email")
    public ResponseEntity<Map<String,Object>> verifyMailOtp(@RequestBody VerifyOtpRequest verifyOtpRequest) {
       if(userService.verifyEmailOtp(verifyOtpRequest.getOtp())) {
           userService.updateUserVerification(verifyOtpRequest.getEmail());
           return ResponseEntity.ok().body(Map.of("status", "success", "message", "Verification success"));
       } else{
           return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "Invalid OTP", "status", 500));
       }
    }

    @PostMapping("/refresh")
    public ResponseEntity<Map<String,Object>> getNewAccessToken(@RequestBody @Valid RefreshTokenRequest refreshTokenRequest) {
        String email = jwtService.extractEmail(refreshTokenRequest.refreshToken());
        if(Objects.isNull(email)) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(Map.of("error", "Invalid or expired refresh token"));
        }
        Map<String,Object> accessToken = jwtService.generateAccessToken(email);
        return ResponseEntity.ok().body(accessToken);
    }

    @PostMapping("/logout")
    public ResponseEntity<Map<String,Object>> logout(@RequestBody AccessTokenRequest accessTokenRequest) {
        jwtService.addTokenToBlackList(accessTokenRequest.getAccessToken());
        return ResponseEntity.ok().body(Map.of("message","logout successful"));
    }

    @GetMapping("/ping")
    public String ping() {
        return "alive";
    }
}
