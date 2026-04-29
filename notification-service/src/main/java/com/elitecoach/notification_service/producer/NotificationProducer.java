package com.elitecoach.notification_service.producer;

import com.elitecoach.notification_service.request.EmailRequest;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class NotificationProducer {

    @Autowired
    private RabbitTemplate rabbitTemplate;


    public void handleEmailNotification(String routingKey, EmailRequest emailRequest) {
        rabbitTemplate.convertAndSend("email-exchange",
                routingKey, emailRequest);
    }
}
