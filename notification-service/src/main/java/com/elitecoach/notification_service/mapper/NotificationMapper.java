package com.elitecoach.notification_service.mapper;

import com.elitecoach.notification_service.dto.NotificationRequest;
import com.elitecoach.notification_service.model.Notification;
import org.modelmapper.ModelMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Objects;

@Service
public class NotificationMapper {

    @Autowired
    private ModelMapper mapper;


    public Notification convertToModel(NotificationRequest notificationRequest) {
        if(!Objects.isNull(notificationRequest))
            return mapper.map(notificationRequest,Notification.class);
        else
            throw new RuntimeException("Invalid user details");
    }

    public NotificationRequest convertToRequest(Notification notification) {
        if(!Objects.isNull(notification))
            return mapper.map(notification,NotificationRequest.class);
        else
            throw new RuntimeException("Invalid user details");
    }
}
