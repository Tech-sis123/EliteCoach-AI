package org.identity_service.EliteCoach.service;

import lombok.extern.slf4j.Slf4j;
import org.identity_service.EliteCoach.dto.UserRequest;
import org.identity_service.EliteCoach.handler.exceptions.UserNotFoundException;
import org.identity_service.EliteCoach.mapper.UserMapper;
import org.identity_service.EliteCoach.model.User;
import org.identity_service.EliteCoach.repository.UserRepository;
import org.identity_service.EliteCoach.request.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

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

    private final Map<String, UserRequest>  userCache;
    private final Map<String, User> dbCache;

    public UserService() {
        userCache = new ConcurrentHashMap<>();
        dbCache = new ConcurrentHashMap<>();
    }

    public Map<String,Object> createUser(UserRequest userRequest) {
        if(dbCache.containsKey(userRequest.getEmail())) {
            return Map.of("message","User account already exists, choose a unique email",
                    "status", "failed");
        }

        User user = userMapper.convertToModel(userRequest);
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        userRepository.save(user);

        Map<String,Object> data = new LinkedHashMap<>();
        data.put("userId", user.getUserId());
        data.put("persona", user.getUserType());
        data.put("isVerified", user.getEmailVerified());

        System.out.println(user);
        //send email notification (otp)
        ChannelRequest channelRequest = new ChannelRequest();
        channelRequest.setChannel("email");
        channelRequest.setTo(userRequest.getEmail());
        channelRequest.setSubject("EliteCoach Account Verification");
        channelRequest.setBody("Verify your EliteCoach Account, Your OTP Is: ".concat(notificationService.generateOTP()));
        notificationService.sendOTP(channelRequest);

        if(!userCache.containsKey(user.getEmail())) {
            userCache.put(user.getEmail(), userMapper.convertToRequest(user));
            dbCache.put(user.getEmail(), user);
        }
        return Map.of("message","User created successfully",
                "status", "success","data",data);
    }

    public Map<String,Object> resetPassword(PasswordResetRequest passwordResetRequest) {
        User user = userRepository.findByEmail(passwordResetRequest.getEmail())
                .orElseThrow(() -> new UserNotFoundException("User account dont exists"));
        if(passwordEncoder.matches(passwordResetRequest.getOldPassword(), user.getPassword())) {
            user.setPassword(passwordEncoder.encode(passwordResetRequest.getNewPassword()));
            userRepository.save(user);
        }
        return Map.of("status", "success", "message", "password reset successful");
    }


    public UserRequest getUserProfile(String email) {
        if(userCache.containsKey(email)) {
            return userCache.get(email);
        } else {
            UserRequest userRequest = userRepository.
                    findByEmail(email).map(userMapper::convertToRequest).
                    orElseThrow(() -> new UserNotFoundException("User not found"));
            userCache.put(email, userRequest);
            return userRequest;
        }
    }

    public User getUser(String email) {
        if(dbCache.containsKey(email)) {
            return dbCache.get(email);
        } else {
            User user = userRepository.
                    findByEmail(email).orElseThrow(() -> new
                            UserNotFoundException("User not found"));
            dbCache.put(email, user);
            return user;
        }
    }

    public void updateUserVerification(String email) {
        User user = userRepository.findByEmail(email).orElseThrow(() ->
                new UserNotFoundException("User account dont exists"));
        user.setEmailVerified(true);

        userRepository.save(user);
    }

    public boolean verifyEmailOtp(String requestOtp) {
        return notificationService.verifyEmailOtp(requestOtp);
    }
}
