package org.identity_service.EliteCoach.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.identity_service.EliteCoach.request.ChannelRequest;
import org.identity_service.EliteCoach.request.WhatsappRequest;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;
import java.util.Random;

@Service
public class NotificationService {

    private String keepOtp;
    @Autowired
    private WebClient webClient;
    @Autowired
    private ObjectMapper objectMapper;
    @Value("${NOTIFICATION-SERVICE.BASE_URL}")
    private String notificationServiceBaseUrl;

    public @Nullable Map sendOTP(ChannelRequest channelRequest) {
        try {
            return webClient.post()
                    .uri(notificationServiceBaseUrl+"/api/v1/notification/send")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(channelRequest)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();
        } catch (RuntimeException e) {
            throw new RuntimeException(e);
        }
    }

    public boolean verifyEmailOtp(String requestOtp) {
        return keepOtp.equals(requestOtp);
    }

    public String generateOTP() {
        Random r = new Random();
        String otp = "";
        for(int i = 0; i < 4; i++) {
            otp += r.nextInt(10);
        }
        keepOtp = otp;
        return otp;
    }
}
