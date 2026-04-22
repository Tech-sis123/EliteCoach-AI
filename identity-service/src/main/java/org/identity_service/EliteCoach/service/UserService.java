package org.identity_service.EliteCoach.service;

import lombok.extern.slf4j.Slf4j;
import org.identity_service.EliteCoach.dto.UserRequest;
import org.identity_service.EliteCoach.mapper.UserMapper;
import org.identity_service.EliteCoach.model.User;
import org.identity_service.EliteCoach.repository.UserRepository;
import org.identity_service.EliteCoach.request.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;

@Slf4j
@Service
public class UserService {

    @Autowired
    private PasswordEncoder passwordEncoder;
    @Autowired
    private UserMapper userMapper;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private NotificationService notificationService;

    public Map<String,Object> createUser(UserRequest userRequest) {
        User user = userMapper.convertToModel(userRequest);
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        userRepository.save(user);
        Map<String,Object> data = new LinkedHashMap<>();
        data.put("userId", user.getUserId());
        data.put("persona", user.getUserType());
        data.put("isVerified", user.getEmailVerified());

        //send email notification (otp)
        EmailRequest emailRequest = new EmailRequest();
        emailRequest.setTo(userRequest.getEmail());
        emailRequest.setSubject("EliteCoach Account Verification");
        emailRequest.setBody("Verify your EliteCoach Account, Your OTP Is: ".concat(notificationService.generateOTP()));
        notificationService.sendOTPViaEmail(emailRequest);

        return Map.of("message","User created successfully",
                "status", "success","data",data);
    }

    public Map<String,Object> resetPassword(PasswordResetRequest passwordResetRequest) {
        User user = userRepository.findByEmail(passwordResetRequest.getEmail())
                .orElseThrow(() -> new RuntimeException("User account dont exists"));
        if(passwordEncoder.matches(passwordResetRequest.getOldPassword(), user.getPassword())) {
            user.setPassword(passwordEncoder.encode(passwordResetRequest.getNewPassword()));
            userRepository.save(user);
        }
        return Map.of("status", "success", "message", "password reset successful");
    }


    public UserRequest getUserProfile(String email) {
        return userRepository.findByEmail(email).map(userMapper::convertToRequest).orElseThrow(() -> new RuntimeException("User not found"));
    }

    public User getUser(String email) {
        return userRepository.findByEmail(email).orElseThrow(() -> new RuntimeException("User not found"));
    }

    public void updateUserVerification(String email) {
        User user = userRepository.findByEmail(email).orElseThrow(() -> new RuntimeException("User account dont exists"));
        user.setEmailVerified(true);

        userRepository.save(user);
    }

    public boolean verifyEmailOtp(String requestOtp) {
        return notificationService.verifyEmailOtp(requestOtp);
    }
}
