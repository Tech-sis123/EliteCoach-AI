package com.elitecoach.notification_service.service;

import com.elitecoach.notification_service.request.UserRequest;
import com.elitecoach.notification_service.response.AccessTokenResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Base64;

@Service
public class UserService {

    @Autowired
    private WebClient webClient;
    @Value("${services.identity-service.url}")
    private String identityServiceBaseUrl;

    public UserRequest getUserProfile(String auth) {
        return webClient.get()
                .uri(identityServiceBaseUrl+"/api/v1/users/profile")
                .header("Authorization", "Bearer " + auth)
                .retrieve()
                .bodyToMono(UserRequest.class)
                .block();
    }
}
