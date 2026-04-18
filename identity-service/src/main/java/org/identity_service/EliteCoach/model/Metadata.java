package org.identity_service.EliteCoach.model;

import lombok.Data;

import java.util.List;

@Data
public class Metadata {

    private String bio;
    private List<String> skills;
    private boolean whatsappNotifications;
    private String emailDigest;
    private boolean lowBandwidthMode;

}
