package org.identity_service.EliteCoach.model;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "course_assignments", schema = "organizations")
public class CourseAssignment {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne
    @JoinColumn(name = "organization_id", nullable = false)
    private Organization organization;

    @Column(name = "course_id", nullable = false)
    private UUID courseId;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "assigned_learners", columnDefinition = "jsonb")
    private List<UUID> assignedLearners;

    private LocalDateTime deadline;

    @CreationTimestamp
    private LocalDateTime assignmentDate;
}