package com.elitecoach.notification_service.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import lombok.Data;

@Data
@Entity
public class Notification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private boolean emailEnabled;
    private boolean whatsappEnabled;
    private boolean smsEnabled;
    private boolean pushEnabled;
    private String preferLanguage;
    private String email;
}
