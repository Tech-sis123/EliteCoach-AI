package com.elitecoach.notification_service.request;


import lombok.Data;

import java.util.UUID;

@Data
public class UserRequest {

    private String firstName;

    private String lastName;
    private String password;
    private String email;
    private UserType userType;
    private UUID organizationId;


}
