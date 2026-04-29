package com.elitecoach.notification_service.configuration;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.support.converter.JacksonJsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

    public static final String QUEUE_NAME = "notification-queue";
    public static final String EXCHANGE_NAME = "elite-coach-events";
    public static final String ROUTING_PATTERN = "learner.#"; // Listens to all learner events

    @Bean
    public Queue notificationQueue() {
        return new Queue(QUEUE_NAME, true);
    }

    @Bean
    public Queue emailQueue() {
        return new Queue("email-queue", true);
    }


    @Bean
    public TopicExchange exchange() {
        return new TopicExchange(EXCHANGE_NAME);
    }

    @Bean
    public TopicExchange emailExchange() {
        return new TopicExchange("email-exchange");
    }

    @Bean
    public Binding binding() {
        return BindingBuilder.bind(notificationQueue()).to(exchange()).with(ROUTING_PATTERN);
    }

    @Bean
    public Binding emailBinding() {
        return BindingBuilder.bind(emailQueue()).to(emailExchange()).with("email.#");
    }
}