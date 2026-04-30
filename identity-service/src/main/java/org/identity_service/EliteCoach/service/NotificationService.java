package org.identity_service.EliteCoach.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.identity_service.EliteCoach.configuration.RabbitMQConfig;
import org.identity_service.EliteCoach.producer.RabbitMQProducer;
import org.identity_service.EliteCoach.request.ChannelRequest;
import org.identity_service.EliteCoach.request.EmailRequest;
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
    @Autowired
    private RabbitMQProducer rabbitMQProducer;

    public void sendOTP(ChannelRequest channelRequest) {
        EmailRequest emailRequest =
                new EmailRequest(channelRequest.getTo(), channelRequest.getSubject(),  channelRequest.getBody());
        rabbitMQProducer.handleEmailNotification("email.send", emailRequest);
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
