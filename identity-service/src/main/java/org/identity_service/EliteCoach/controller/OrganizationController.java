package org.identity_service.EliteCoach.controller;

import lombok.RequiredArgsConstructor;
import org.identity_service.EliteCoach.dto.OrganizationDTOs;
import org.identity_service.EliteCoach.service.OrganizationService;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/organizations")
@RequiredArgsConstructor
public class OrganizationController {

    private final OrganizationService orgService;

    @PostMapping
    public ResponseEntity<OrganizationDTOs.CreateOrgResponse> createOrganization(@RequestBody OrganizationDTOs.CreateOrgRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(orgService.createOrg(request));
    }

    @GetMapping("/{organizationId}")
    public ResponseEntity<OrganizationDTOs.OrgDetailsResponse> getOrganization(@PathVariable UUID organizationId) {
        return ResponseEntity.ok(orgService.getOrgDetails(organizationId));
    }

    @PostMapping(value = "/{organizationId}/import-learners", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<OrganizationDTOs.ImportResponse> importLearners(
            @PathVariable UUID organizationId,
            @RequestParam("csvFile") MultipartFile file) {
        return ResponseEntity.ok(orgService.importLearners(organizationId, file));
    }

    @PostMapping("/{organizationId}/assign-course")
    public ResponseEntity<Map<String, Object>> assignCourse(
            @PathVariable UUID organizationId,
            @RequestBody OrganizationDTOs.CourseAssignmentRequest request) {
        return ResponseEntity.ok(orgService.assignCourse(organizationId, request));
    }

    @GetMapping("/{organizationId}/dashboard")
    public ResponseEntity<OrganizationDTOs.DashboardStats> getDashboard(@PathVariable UUID organizationId) {
        return ResponseEntity.ok(orgService.getDashboardStats(organizationId));
    }

    @GetMapping("/{organizationId}/reports/learner-progress")
    public ResponseEntity<Map<String, Object>> getProgressReport(
            @PathVariable UUID organizationId,
            @RequestParam(required = false) LocalDateTime startDate,
            @RequestParam(required = false) LocalDateTime endDate,
            @RequestParam String format) {
        return ResponseEntity.ok(orgService.generateProgressReport(organizationId, startDate, endDate, format));
    }

    @GetMapping("/{organizationId}/reports/compliance")
    public ResponseEntity<Map<String, Object>> getComplianceReport(@PathVariable UUID organizationId) {
        return ResponseEntity.ok(orgService.generateComplianceReport(organizationId));
    }
}