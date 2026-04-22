package org.identity_service.EliteCoach.service;

import com.opencsv.CSVReader;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.identity_service.EliteCoach.dto.OrganizationDTOs;
import org.identity_service.EliteCoach.dto.UserRequest;
import org.identity_service.EliteCoach.model.Organization;
import org.identity_service.EliteCoach.model.PlanTier;
import org.identity_service.EliteCoach.model.User;
import org.identity_service.EliteCoach.repository.OrganizationRepository;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.Reader;
import java.time.LocalDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
public class OrganizationService {

    private final OrganizationRepository orgRepo;
    @Autowired
    private UserService userService;
    // Inject LearnerRepository, CourseRepository, etc.

    public OrganizationDTOs.CreateOrgResponse createOrg(OrganizationDTOs.CreateOrgRequest req, String adminEmail) {
        // Save to DB and return response
        Organization organization =  createOrganization(req,adminEmail);

        return OrganizationDTOs.CreateOrgResponse.builder()
                .organizationId(organization.getId()) // Replace with saved entity ID
                .planTier(organization.getPlanTier().name())
                .maxLearners(organization.getMaxLearners())
                .createdAt(LocalDateTime.now())
                .build();
    }

    public OrganizationDTOs.ImportResponse importLearners(UUID orgId, MultipartFile file) {
        List<OrganizationDTOs.ImportError> errorList = new ArrayList<>();
        int successCount = 0;

        try (Reader reader = new BufferedReader(new InputStreamReader(file.getInputStream()))) {
            // This tool reads the CSV line by line
            CSVReader csvReader = new CSVReader(reader);
            String[] row; // <--- This is where the variable 'row' is defined

            // Skip the header row if your CSV has one
            csvReader.readNext();

            while ((row = csvReader.readNext()) != null) {
                // Logic: row[0] = email, row[1] = firstName, row[2] = lastName
                String email = row[0];

                if (isValidEmail(email)) {
                    // TODO: Save to database using LearnerRepository : call learner service to create learner and associate with orgId
                    successCount++;
                } else {
                    // If invalid, add to our error bucket
                    errorList.add(new OrganizationDTOs.ImportError(email, "Invalid email format"));
                }
            }
        } catch (Exception e) {
            throw new RuntimeException("Failed to parse CSV file: " + e.getMessage());
        }

        return OrganizationDTOs.ImportResponse.builder()
                .imported(successCount)
                .failed(errorList.size())
                .errors(errorList)
                .build();
    }

    private boolean isValidEmail(String email) {
        return email != null && email.contains("@"); // Simple check
    }

    public OrganizationDTOs.DashboardStats getDashboardStats(UUID orgId) {
        // Here you would perform aggregations (JPQL or Native Queries)
        // Calculating completionRate and averageScore for the organization
        return OrganizationDTOs.DashboardStats.builder()
                .activeLearners(120)
                .completionRate(75.5)
                .averageScore(82.0)
                .build();
    }

    public OrganizationDTOs.OrgDetailsResponse getOrgDetails(UUID organizationId) {
        // 1. Fetch the organization from the database or throw 404
        Organization org = orgRepo.findById(organizationId)
                .orElseThrow(() -> new EntityNotFoundException("Organization not found with ID: " + organizationId));

        // 2. Map the Entity data to your DTO using the Builder pattern
        return OrganizationDTOs.OrgDetailsResponse.builder()
                .organizationId(org.getId())
                .name(org.getName())
                .maxLearners(org.getMaxLearners()) // You would typically fetch this from the learning service
                // These would typically come from related repositories or counts
                .activeLearnersCount(0)
                .courses(new ArrayList<>()) // Replace with actual course mapping logic
                .administrators(new ArrayList<>()) // Replace with actual admin mapping
                .build();
    }

    public Map<String, Object> assignCourse(UUID organizationId, OrganizationDTOs.CourseAssignmentRequest request) {
        // 1. Verify organization exists
        Organization org = orgRepo.findById(organizationId)
                .orElseThrow(() -> new EntityNotFoundException("Organization not found"));

        // 2. Logic: In a real app, you would save these assignments to a 'CourseAssignment' table
        // For now, we simulate the response expected by your API contract
        int learnersCount = request.getLearnersOrTeamIds() != null ? request.getLearnersOrTeamIds().size() : 0;

        Map<String, Object> response = new HashMap<>();
        response.put("assignmentId", UUID.randomUUID());
        response.put("learnersAssigned", learnersCount);
        response.put("status", "SUCCESS");

        return response;
    }
    public Map<String, Object> generateProgressReport(UUID organizationId, LocalDateTime startDate, LocalDateTime endDate, String format) {
        // 1. Verify organization exists
        orgRepo.findById(organizationId)
                .orElseThrow(() -> new jakarta.persistence.EntityNotFoundException("Organization not found"));

        // 2. Logic: In production, you would trigger a background job to generate a PDF/Excel
        Map<String, Object> response = new HashMap<>();
        response.put("reportUrl", "https://s3.amazonaws.com/elite-coach-reports/progress-" + UUID.randomUUID() + "." + format);
        response.put("format", format.toUpperCase());
        response.put("generatedAt", LocalDateTime.now());

        return response;
    }

    public Map<String, Object> generateComplianceReport(UUID organizationId) {
        // 1. Verify organization exists
        orgRepo.findById(organizationId)
                .orElseThrow(() -> new jakarta.persistence.EntityNotFoundException("Organization not found"));

        // 2. Mocking stats for the compliance audit
        Map<String, Object> response = new HashMap<>();
        response.put("learnersWithCertificates", 45); // Example stat
        response.put("completionDeadlines", new HashMap<String, Integer>());
        response.put("auditTrail", "Active");
        response.put("reportUrl", "https://s3.amazonaws.com/elite-coach-reports/compliance-" + UUID.randomUUID() + ".pdf");

        return response;
    }

    public Organization createOrganization(OrganizationDTOs.CreateOrgRequest req, String adminEmail) {
        User user = userService.getUser(adminEmail);
        int maxLearners = switch (req.getPlanTier().toLowerCase()) {
            case "starter" -> 50;
            case "growth" -> 250;
            case "enterprise" -> 1000;
            default -> 10000; // Institutional
        };

        Organization org = new Organization();
        org.setName(req.getName());
        org.setIndustry(req.getIndustry());
        org.setCountry(req.getCountry());
        org.setWebsite(req.getWebsite());
        org.setMaxLearners(maxLearners);
        org.setPlanTier(PlanTier.valueOf(req.getPlanTier()));
        org.setAdminUserId(user.getUserId());

        orgRepo.save(org);

        return org;
    }
}