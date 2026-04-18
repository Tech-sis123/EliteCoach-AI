package org.identity_service.EliteCoach.model;
import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "orgs", schema = "organizations")
@Data
public class Organization {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, unique = true)
    private String name;

    private String industry;
    private String country;
    private String website;

    @Enumerated(EnumType.STRING)
    @Column(name = "plan_tier")
    private PlanTier planTier = PlanTier.starter;

    @Column(name = "admin_user_id", nullable = false)
    private UUID adminUserId;

    @Column(name = "ndpr_dpa_signed")
    private Boolean ndprDpaSigned = false;

    @CreationTimestamp
    private LocalDateTime createdAt;

    // Getters and Setters
}