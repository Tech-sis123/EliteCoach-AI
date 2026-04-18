package com.elitecoach.notification_service.consumer;

import com.elitecoach.notification_service.configuration.RabbitMQConfig;
import com.elitecoach.notification_service.request.EmailRequest;
import com.elitecoach.notification_service.request.WhatsappRequest;
import com.elitecoach.notification_service.service.NotificationService;
import lombok.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
@Slf4j
@RequiredArgsConstructor
public class NotificationConsumer {

    @Autowired
    private NotificationService notificationService;
    // Assume you have a FeignClient or RestTemplate to fetch User info from Identity Service
    // private final IdentityServiceClient identityClient;

    @RabbitListener(queues = RabbitMQConfig.QUEUE_NAME)
    public void handleNotificationEvent(Map<String, Object> eventPayload) {
        log.info("Received Event: {}", eventPayload.get("event"));

        String eventType = (String) eventPayload.get("event");
        String learnerId = (String) eventPayload.get("learner_id");

        // 1. Fetch User details (Phone/Email) from Identity Service using learnerId
        // UserDTO user = identityClient.getUserById(learnerId);

        switch (eventType) {
            case "LEARNER_SESSION_COMPLETED":
                sendSessionSummary(learnerId, eventPayload);
                break;
            case "LEARNER_COURSE_COMPLETED":
                sendCertificateNotification(learnerId, eventPayload);
                break;
            case "ESCALATION_TRIGGERED":
                //notifyHumanTutor(eventPayload);
                break;
        }
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
}