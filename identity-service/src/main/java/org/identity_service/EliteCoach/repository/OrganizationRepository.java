package org.identity_service.EliteCoach.repository;

import org.identity_service.EliteCoach.model.Organization;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface OrganizationRepository extends JpaRepository<Organization, UUID> {
}
