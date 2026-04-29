package org.identity_service.EliteCoach.configuration;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletResponse;
import org.identity_service.EliteCoach.filter.AuthFilter;
import org.identity_service.EliteCoach.filter.JwtFilter;
import org.identity_service.EliteCoach.service.JwtService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.*;

@Configuration
@EnableWebSecurity
public class SecurityConfiguration {

    @Autowired
    private MyUserDetailsService myUserDetailsService;

    @Autowired
    private JwtFilter jwtFilter;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private JwtService jwtService;

    private String[] publicUrls = new String[]{
            "/api/v1/auth/**",
            "/swagger-ui/**",
            "/v3/api-docs/**",
            "/swagger-ui.html",
            "/webjars/**",
            "/favicon.ico",
            "/actuator/**",
            "/error"
    };


    @Bean
    public UserDetailsService userDetailsService() {
        return myUserDetailsService;
    }

    @Bean
    public PasswordEncoder getPasswordEncoder() {
        return new BCryptPasswordEncoder(12);
    }


    @Bean
    public DaoAuthenticationProvider authenticationProvider()  {
        DaoAuthenticationProvider authProvider = new DaoAuthenticationProvider(userDetailsService());
        authProvider.setPasswordEncoder(getPasswordEncoder());
        return authProvider;
    }


    public AuthFilter authFilter(AuthenticationManager authenticationManager) {
        AuthFilter authFilter = new AuthFilter();
        authFilter.setAuthenticationManager(authenticationManager);
        authFilter.setFilterProcessesUrl("/api/v1/auth/login");
        authFilter.setAuthenticationSuccessHandler(((request, response, authentication) -> {
            UserPrincipal userPrincipal = (UserPrincipal) authentication.getPrincipal();
            Map<String,Object> accessToken = jwtService.generateAccessToken(userPrincipal.getUsername());
            Map<String,Object> refreshToken = jwtService.generateRefreshToken(userPrincipal.getUsername());
            response.setContentType("application/json");
            response.setStatus(HttpServletResponse.SC_OK);
            Map<String,Object> data_response =
                    authResponse(accessToken.get("accessToken").toString(), accessToken.get("expiry"),
                            refreshToken.get("refreshToken").toString(), refreshToken.get("expiry"),
                            userPrincipal.getUser().getUserId(),userPrincipal.getUser().getFirstName().concat(" ").concat(userPrincipal.getUser().getLastName()),
                            userPrincipal.getUser().getUserType().toString());

            response.getWriter().write(objectMapper.writeValueAsString(data_response));
        }));
        authFilter.setAuthenticationFailureHandler((request, response, exception) -> {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.getWriter().write(objectMapper.writeValueAsString(Map.of("status", HttpStatus.UNAUTHORIZED, "message", "Invalid login details")));
        });
        return authFilter;
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOriginPatterns(List.of("*"));
        configuration.setAllowedMethods(List.of("GET", "POST", "DELETE", "PUT","OPTIONS"));
        configuration.setAllowCredentials(true);
        configuration.setAllowedHeaders(List.of("*"));

        UrlBasedCorsConfigurationSource urlBasedCorsConfigurationSource = new UrlBasedCorsConfigurationSource();
        urlBasedCorsConfigurationSource.registerCorsConfiguration("/**", configuration);

        return urlBasedCorsConfigurationSource;
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration authenticationConfiguration) {
        return authenticationConfiguration.getAuthenticationManager();
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity httpSecurity, AuthenticationManager authenticationManager) {
        return httpSecurity.cors(cors -> cors.configurationSource(corsConfigurationSource()))
                .csrf(csrf -> csrf.disable())
                .authorizeHttpRequests(requests -> requests.
                        requestMatchers("/api/v1/organizations/**").hasAnyRole("org_admin", "super_admin").
                        requestMatchers(publicUrls)
                        .permitAll().anyRequest().authenticated())
                .addFilterAt(authFilter(authenticationManager), UsernamePasswordAuthenticationFilter.class)
                .addFilterAfter(jwtFilter, UsernamePasswordAuthenticationFilter.class)
                .build();

    }

    public Map<String,Object> authResponse(String accessToken, Object aExpiresIn,
                                           String refreshToken, Object rExpiresIn, UUID userId, String fullname,
                                           String persona) {
        return Map.of("status", "success",
                "accessToken", accessToken,
                "accessToken_expiresIn", aExpiresIn,
                "refreshToken", refreshToken,
                "refreshToken_expiresIn", rExpiresIn,
                    "data", Map.of("userId", userId, "fullname", fullname,
                        "persona", persona));

    }
}
