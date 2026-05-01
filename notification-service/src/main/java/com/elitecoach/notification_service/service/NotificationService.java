package com.elitecoach.notification_service.service;

import com.elitecoach.notification_service.dto.NotificationRequest;
import com.elitecoach.notification_service.mapper.NotificationMapper;
import com.elitecoach.notification_service.model.Notification;
import com.elitecoach.notification_service.producer.NotificationProducer;
import com.elitecoach.notification_service.repsository.NotificationRepository;
import com.elitecoach.notification_service.request.EmailRequest;
import com.elitecoach.notification_service.request.UserRequest;
import com.elitecoach.notification_service.request.WhatsappRequest;
import com.elitecoach.notification_service.response.AccessTokenResponse;
import com.elitecoach.notification_service.response.WhatsappNotificationResponse;
import jakarta.mail.internet.InternetAddress;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.mail.MailException;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import sendinblue.ApiClient;
import sendinblue.ApiException;
import sendinblue.Configuration;
import sendinblue.auth.ApiKeyAuth;
import sibApi.TransactionalEmailsApi;
import sibModel.CreateSmtpEmail;
import sibModel.SendSmtpEmail;
import sibModel.SendSmtpEmailSender;
import sibModel.SendSmtpEmailTo;

import java.io.UnsupportedEncodingException;
import java.util.Base64;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

@Service
@Slf4j
public class NotificationService {

    @Autowired
    private WebClient webClient;
    @Value("${INTERSWITCH.GENERAL_CLIENT_ID}")
    private String GENERAL_CLIENT_ID;
    @Value("${INTERSWITCH.GENERAL_CLIENT_SECRET}")
    private String GENERAL_CLIENT_SECRET;

    @Autowired
    private NotificationRepository notificationRepository;

    @Autowired
    private NotificationMapper notificationMapper;

    @Autowired
    private NotificationProducer notificationProducer;

    @Value("${brevo.api.key}")
    private String BREVO_APIKEY;

    public void sendSimpleMail(EmailRequest emailRequest) {
        notificationProducer.handleEmailNotification("email.send", emailRequest);
    }

    public void sendNotificationEmail(EmailRequest emailRequest) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();

        // Configure API key authorization: api-key
        ApiKeyAuth apiKey = (ApiKeyAuth) defaultClient.getAuthentication("api-key");
        apiKey.setApiKey(BREVO_APIKEY);

        TransactionalEmailsApi apiInstance = new TransactionalEmailsApi();

        SendSmtpEmail sendSmtpEmail = new SendSmtpEmail();
        sendSmtpEmail.setSender(new SendSmtpEmailSender().name("Elite Coach").email("fakorodehenry@gmail.com"));
        sendSmtpEmail.setTo(Collections.singletonList(new SendSmtpEmailTo().email(emailRequest.getTo()).name(emailRequest.getTo())));
        sendSmtpEmail.setSubject(emailRequest.getSubject());
        sendSmtpEmail.setHtmlContent("<html><body><h1>" + emailRequest.getBody() + "</h1><p>Ready to play?</p></body></html>");

        try {
            CreateSmtpEmail result = apiInstance.sendTransacEmail(sendSmtpEmail);
        } catch (ApiException e) {
            // THIS LINE IS CRITICAL
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response body: " + e.getResponseBody());
            e.printStackTrace();
        }
    }

    public void createNotificationPreferences(NotificationRequest notificationRequest, UserRequest userRequest) {
        // Implement logic to save notification preferences to a database or another service
        // This is a placeholder and should be replaced with actual implementation
        if(userRequest == null) {
            throw new RuntimeException("User not found");
        }
        Notification notification = notificationMapper.convertToModel(notificationRequest);
        notification.setEmail(userRequest.getEmail());
        notificationRepository.save(notification);
    }


    public NotificationRequest getNotificationPreferences(String email) {
        // Implement logic to retrieve notification preferences from a database or another service
        // This is a placeholder and should be replaced with actual implementation
        Notification notification = notificationRepository.findByEmail(email).orElseThrow(() -> new RuntimeException("Notification preferences not found"));
        return notificationMapper.convertToRequest(notification);
    }

    public AccessTokenResponse getInterswitchAccessToken(String clientId, String clientSecret) {
        String auth = Base64.getEncoder().encodeToString((clientId + ":" + clientSecret).getBytes());

        return webClient.post()
                .uri("https://qa.interswitchng.com/passport/oauth/token")
                .header("Authorization", "Basic " + auth)
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .body(BodyInserters.fromFormData("grant_type", "client_credentials"))
                .retrieve()
                .bodyToMono(AccessTokenResponse.class)
                .block();
    }

    public WhatsappNotificationResponse sendInterswitchWhatsappNotification(WhatsappRequest whatsappRequest) {
        AccessTokenResponse accessTokenResponse = getInterswitchAccessToken(GENERAL_CLIENT_ID, GENERAL_CLIENT_SECRET);
        String accessToken = accessTokenResponse.getAccess_token();

        // Implement the logic to send notification using Interswitch API with the obtained access token
        // This is a placeholder and should be replaced with actual API call to Interswitch
        Map<String,Object> requestBody = new HashMap<>();
        requestBody.put("phoneNumber", whatsappRequest.getWhatsappNumber());
        requestBody.put("service", "EliteCoach AI");
        requestBody.put("code", whatsappRequest.getMessage());
        requestBody.put("action", "verifying");
        requestBody.put("channel","phone");

        return webClient.post()
                .uri("https://api-marketplace-routing.k8.isw.la/marketplace-routing/api/v1/whatsapp/auth/send")
                .header("Authorization", "Bearer " + accessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(WhatsappNotificationResponse.class)
                .block();
    }
}
