package org.identity_service.EliteCoach.configuration;


import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeIn;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Contact;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.info.License;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import io.swagger.v3.oas.annotations.servers.Server;

@OpenAPIDefinition(
        info = @Info(
                title = "EliteCoach-Identity Service API Documentation",
                version = "1.0",
                description = "API documentation for the EliteCoach-Identity Service application",
                contact = @Contact(
                        name = "Fakorode Henry",
                        email = "fakorodehenry@gmail.com",
                        url = "https://henry-portfolio-rosy.vercel.app/"
                ),
                license = @License(
                        name = "EliteCoach License"
                ),
                termsOfService = "Terms Of Service for EliteCoach-Identity Service API"
        ),
        servers = {
                @Server(
                        url = "http://localhost:8080",
                        description = "Local development server"
                ),
                @Server(
                        url = "https://elitecoach-ai-oxax.onrender.com",
                        description = "Production development server"
                )
        }
        ,
        security = @SecurityRequirement(name = "EliteCoach Auth")
)
@SecurityScheme(
        name = "EliteCoach Auth",
        type = SecuritySchemeType.HTTP,
        scheme = "bearer",
        bearerFormat = "jwt",
        in = SecuritySchemeIn.HEADER,
        description = "EliteCoach JWT Authentication"
)

public class OpenApiConfiguration {
}
