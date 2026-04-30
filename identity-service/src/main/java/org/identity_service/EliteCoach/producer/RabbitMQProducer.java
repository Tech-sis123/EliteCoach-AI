package org.identity_service.EliteCoach.producer;

import org.identity_service.EliteCoach.request.EmailRequest;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class RabbitMQProducer {

    @Autowired
    private RabbitTemplate rabbitTemplate;


    public void handleEmailNotification(String routingKey, EmailRequest emailRequest) {
        rabbitTemplate.convertAndSend("email-exchange",
                routingKey, emailRequest);
    }
}
