package com.elitecoach.notification_service.repsository;

import com.elitecoach.notification_service.model.Notification;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface NotificationRepository extends JpaRepository<Notification, Long> {
    Optional<Notification> findByEmail(String email);
}
