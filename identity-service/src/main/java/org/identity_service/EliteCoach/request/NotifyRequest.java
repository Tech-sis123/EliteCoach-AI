package org.identity_service.EliteCoach.request;

import lombok.Data;

@Data
public class NotifyRequest {

    private boolean whatsappNotifications;
    private String emailDigest;
    private boolean lowBandwidthMode;
}
