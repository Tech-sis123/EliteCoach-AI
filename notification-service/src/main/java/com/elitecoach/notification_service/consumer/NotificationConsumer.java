package com.elitecoach.notification_service.consumer;

import com.elitecoach.notification_service.configuration.RabbitMQConfig;
import com.elitecoach.notification_service.request.EmailRequest;
import com.elitecoach.notification_service.request.WhatsappRequest;
import com.elitecoach.notification_service.service.MessageBodyService;
import com.elitecoach.notification_service.service.NotificationService;
import com.sendgrid.Method;
import com.sendgrid.Request;
import com.sendgrid.Response;
import com.sendgrid.SendGrid;
import com.sendgrid.helpers.mail.Mail;
import com.sendgrid.helpers.mail.objects.Content;
import com.sendgrid.helpers.mail.objects.Email;
import lombok.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.AmqpRejectAndDontRequeueException;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.MailException;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.Map;

@Service
@Slf4j
public class NotificationConsumer {

    @Autowired
    private NotificationService notificationService;
    @Autowired
    private MessageBodyService messageBodyService;

    private final SendGrid sendGrid;

    // Inject the SendGrid bean (configured in a @Configuration class)
    public NotificationConsumer(SendGrid sendGrid) {
        this.sendGrid = sendGrid;
    }

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

    @RabbitListener(queues = "#{emailQueue.name}")
    public void sendNotificationEmail(EmailRequest emailRequest) {
        Email from = new Email("notifications@yourdomain.com");
        Email to = new Email(emailRequest.getTo());
        Content content = new Content("text/plain", emailRequest.getBody());
        Mail mail = new Mail(from, emailRequest.getSubject(), to, content);

        Request request = new Request();
        try {
            request.setMethod(Method.POST);
            request.setEndpoint("mail/send");
            request.setBody(mail.build());

            Response response = sendGrid.api(request);

            if (response.getStatusCode() >= 400) {
                log.error("SendGrid error: {} - {}", response.getStatusCode(), response.getBody());
                // Optionally throw an exception here to trigger RabbitMQ retries
            }
        } catch (IOException ex) {
            log.error("Failed to send email due to network error", ex);
            throw new AmqpRejectAndDontRequeueException(ex); // Send to Dead Letter Queue
        }
    }
}