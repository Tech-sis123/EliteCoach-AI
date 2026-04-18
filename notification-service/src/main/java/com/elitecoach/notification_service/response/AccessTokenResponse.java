package com.elitecoach.notification_service.response;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class AccessTokenResponse {


    private String access_token;
    private String token_type;
    private int expires_in;
    private String scope;
    private String marketplace_user;
    private String client_name;
    private String client_logo;
    private String client_description;
    private String[] api_routing_actions;
    private String jti;

}
