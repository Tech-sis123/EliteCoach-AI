package org.identity_service.EliteCoach.model;

import jakarta.persistence.Embeddable;
import lombok.Data;

@Embeddable
@Data
public class UserProfile {

    private String avatarUrl;
    private Metadata metadata;
}
