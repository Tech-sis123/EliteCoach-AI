package org.identity_service.EliteCoach.repository;

import jakarta.validation.constraints.Email;
import org.identity_service.EliteCoach.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface UserRepository extends JpaRepository<User, UUID> {

    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);
}
