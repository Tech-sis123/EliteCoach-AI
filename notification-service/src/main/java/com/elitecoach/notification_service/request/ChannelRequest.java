package com.elitecoach.notification_service.request;

import lombok.Data;

@Data
public class ChannelRequest {

    private String channel;
    private String body;
    private String to;
    private String subject;
}
