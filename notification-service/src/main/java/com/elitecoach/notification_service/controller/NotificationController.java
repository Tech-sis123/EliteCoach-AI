package com.elitecoach.notification_service.controller;

import com.elitecoach.notification_service.dto.NotificationRequest;
import com.elitecoach.notification_service.request.ChannelRequest;
import com.elitecoach.notification_service.request.EmailRequest;
import com.elitecoach.notification_service.request.UserRequest;
import com.elitecoach.notification_service.request.WhatsappRequest;
import com.elitecoach.notification_service.service.NotificationService;
import com.elitecoach.notification_service.service.UserService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@CrossOrigin(origins = {"https://elite-coach-seven.vercel.app", "http://localhost:8080"})
@RequestMapping("/api/v1/notification")
public class NotificationController {

    @Autowired
    private NotificationService notificationService;

    @Autowired
    private UserService userService;
    @PostMapping("/send")
    public ResponseEntity<Map<String, Object>> sendNotification(@RequestBody ChannelRequest channelRequest, HttpServletRequest request) {
        if(channelRequest.getChannel().equalsIgnoreCase("email")) {
            EmailRequest emailRequest = EmailRequest.builder()
                    .body(channelRequest.getBody())
                    .to(channelRequest.getTo())
                    .subject(channelRequest.getSubject())
                    .build();
            notificationService.sendSimpleMail(emailRequest);
        } else if(channelRequest.getChannel().equalsIgnoreCase("whatsapp")) {
            WhatsappRequest whatsappRequest = WhatsappRequest.builder()
                    .whatsappNumber(channelRequest.getTo())
                    .message(channelRequest.getBody())
                    .build();
            notificationService.sendInterswitchWhatsappNotification(whatsappRequest);
        } else {
            return ResponseEntity.badRequest().body(Map.of("message", "Invalid notification channel"));
        }

        return ResponseEntity.ok().body(Map.of("message", "Notification sent successfully"));
    }

    @PostMapping("/preferences")
    public ResponseEntity<Map<String, Object>> setNotificationPreferences(@RequestBody NotificationRequest preferences, HttpServletRequest request) {
        String auth = fetchAuthToken(request);
        UserRequest userRequest = userService.getUserProfile(auth);
        notificationService.createNotificationPreferences(preferences, userRequest);
        // Here you would typically save the preferences to a database or another service
        // For this example, we'll just return the preferences back in the response

        return ResponseEntity.ok().body(Map.of("message", "Notification preferences updated successfully", "preferences", preferences, "preferencesUpdated",true));
    }


    public String fetchAuthToken(HttpServletRequest servletRequest) {
        String header = servletRequest.getHeader("Authorization");
        String token = null;
        if(header != null) {
            token = header.substring(7);
        }
        return token;
    }

    @GetMapping("/ping")
    public String ping() {
        return "alive";
    }
}
