package com.elitecoach.notification_service.consumer;

import com.elitecoach.notification_service.configuration.RabbitMQConfig;
import com.elitecoach.notification_service.request.EmailRequest;
import com.elitecoach.notification_service.request.WhatsappRequest;
import com.elitecoach.notification_service.service.MessageBodyService;
import com.elitecoach.notification_service.service.NotificationService;
import jakarta.annotation.PostConstruct;
import jakarta.mail.internet.InternetAddress;
import lombok.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.MailException;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;
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
import java.util.Collections;
import java.util.Map;

@Service
@Slf4j
@RequiredArgsConstructor
public class NotificationConsumer {

    @Autowired
    private NotificationService notificationService;
    @Autowired
    private MessageBodyService messageBodyService;
    @Autowired
    private JavaMailSender javaMailSender;
    @Value("${spring.mail.username}")
    private String fromEmail;
    @Value("${brevo.api.key}")
    private String BREVO_APIKEY;
    // Assume you have a FeignClient or RestTemplate to fetch User info from Identity Service
    // private final IdentityServiceClient identityClient;


    @RabbitListener(queues = RabbitMQConfig.QUEUE_NAME)
    public void handleEvent(Map<String, Object> event) {

        String eventType = (String) event.get("event");

        String emailBody = switch (eventType) {
            case "LEARNER_SESSION_STARTED" -> messageBodyService.buildSessionStartedEmail(event);
            case "LEARNER_SESSION_COMPLETED" -> messageBodyService.buildSessionCompletedEmail(event);
            case "LEARNER_COURSE_COMPLETED" -> messageBodyService.buildCourseCompletedEmail(event);
            case "ESCALATION_TRIGGERED" -> messageBodyService.buildEscalationEmail(event);
            case "AI_RESPONSE_GENERATED" -> messageBodyService.buildAIResponseEmail(event);
            default -> "Unknown event received";
        };

        System.out.println("Received Event: " + event);
        System.out.println("Generated Email Body: " + emailBody);
    }

    private void handleAIResponse(Map<String, Object> event) {
        System.out.println("AI Response Generated: " + event);
    }

    private void sendSessionSummary(String learnerId, Map<String, Object> data) {
        String msg = "Great job finishing your session on " + data.get("course_id") + "!";
        WhatsappRequest whatsappRequest = WhatsappRequest.builder()
                .whatsappNumber(data.get("whatsappNumber").toString()) // Phone fetched from Identity Service
                .message(msg)
                .build();
        notificationService.sendInterswitchWhatsappNotification(whatsappRequest); // Phone fetched from Identity Service
        log.info("WhatsApp Summary Sent to {}", learnerId);
    }

    private void sendCertificateNotification(String learnerId, Map<String, Object> data) {
        String msg = "Congratulations on completing " + data.get("course_id") + "! Your certificate is ready.";
        EmailRequest emailRequest = EmailRequest.builder()
                        .body(msg)
                        .to(data.get("email").toString()) // Email fetched from Identity Service
                        .subject("Course Completion Certificate")
                        .build();

        notificationService.sendSimpleMail(emailRequest);
    }

    @RabbitListener(queues = "email-queue")
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
            System.out.println("Email sent successfully: " + result.getMessageId());
        } catch (ApiException e) {
            System.err.println("Exception when calling TransactionalEmailsApi#sendTransacEmail");
            e.printStackTrace();
        }
    }
}