package org.identity_service.EliteCoach.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Data
public class OrganizationDTOs {

    @Data
    public static class CreateOrgRequest {
        private String name;
        private String industry;
        private String country;
        private String website;
        private String planTier;
    }

    @Data @Builder
    public static class CreateOrgResponse {
        private UUID organizationId;
        private String planTier;
        private int maxLearners;
        private LocalDateTime createdAt;
    }

    @Data @Builder
    public static class OrgDetailsResponse {
        private UUID organizationId;
        private String name;
        private String planTier;
        private long activeLearnersCount;
        private int maxLearners;
        private List<Object> courses; // Replace Object with Course entity
        private List<Object> administrators; // Replace Object with User entity
    }

    @Data
    @Builder
    public static class ImportResponse {
        private int imported;
        private int failed;
        private List<ImportError> errors;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ImportError {
        private String learnerId; // This could be the email or row number from the CSV
        private String error;     // e.g., "Invalid email format" or "User already exists"
    }

    @Data
    public static class CourseAssignmentRequest {
        private UUID courseId;
        private List<UUID> learnersOrTeamIds;
        private LocalDateTime deadline;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DashboardStats {
        private long activeLearners;
        private double completionRate;
        private double averageScore;
        private int atRiskLearners;
        // This will now resolve correctly
        private List<CourseProgress> courseProgress;
    }



    // Additional inner classes: ImportError, CourseProgress, etc.
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CourseProgress {
        private UUID courseId;
        private double completionRate;
        private int enrolledCount;
    }
}
