package com.elitecoach.notification_service.configuration;


import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Contact;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.info.License;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.servers.Server;

@OpenAPIDefinition(
        info = @Info(
                title = "EliteCoach-Notification Service API Documentation",
                version = "1.0",
                description = "API documentation for the EliteCoach-Notification Service application",
                contact = @Contact(
                        name = "Fakorode Henry",
                        email = "fakorodehenry@gmail.com",
                        url = "https://henry-portfolio-rosy.vercel.app/"
                ),
                license = @License(
                        name = "EliteCoach License"
                ),
                termsOfService = "Terms Of Service for EliteCoach-Notification Service API"
        ),
        servers = {
                @Server(
                        url = "http://localhost:8080",
                        description = "Local development server"
                ),
                @Server(
                        url = "https://elitecoach.onrender.com",
                        description = "Production development server"
                )
        })
public class OpenApiConfiguration {
}
