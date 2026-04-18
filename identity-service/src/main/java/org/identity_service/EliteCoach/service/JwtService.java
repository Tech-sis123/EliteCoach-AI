package org.identity_service.EliteCoach.service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.function.Function;

import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.UnsupportedJwtException;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.SecurityException;

@Service
public class JwtService {

    // default token validity in minutes
    @Value("${jwt.accessTokenMinutes:15}")
    private long accessTokenMinutes;

    @Value("${jwt.accessTokenMinutes:10080}")
    private long refreshTokenMinutes;

    private SecretKey signingKey;

    private Set<String> blacklist_tokens = new LinkedHashSet<>();

    public JwtService() {
        KeyGenerator  keyGenerator = null;
        try {
            keyGenerator = KeyGenerator.getInstance("HmacSHA256");
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
        signingKey = keyGenerator.generateKey();
    }

    // Generate an access token with default validity and subject=email
    public Map<String, Object> generateAccessToken(String email) {
        return generateToken(Map.of(), email, accessTokenMinutes);
    }

    // Generate refresh token with default validity and subject=email
    public Map<String, Object> generateRefreshToken(String email) {
        return generateToken(Map.of(), email, refreshTokenMinutes);
    }

    // Generate token with extra claims and custom validity (minutes)
    public Map<String,Object> generateToken(Map<String, Object> extraClaims, String email, long minutesValid) {
        Date now = new Date(System.currentTimeMillis());
        long expiryMillis = minutesValid *  60 * 1000;
        Date expiry = new Date(System.currentTimeMillis() + expiryMillis);
        String accessToken = Jwts.builder()
                .claims(extraClaims)
                .subject(email)
                .issuedAt(now)
                .expiration(expiry)
                .signWith(getKey())
                .compact();
        return Map.of("accessToken", accessToken,"expiry", expiry);
    }

    public SecretKey getKey() {
        return Keys.hmacShaKeyFor(Base64.getEncoder().encode(signingKey.getEncoded()));
    }

    // Extract subject (email)
    public String extractEmail(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    public Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }

    // Generic extractor
    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        Claims claims = parseClaims(token);
        if (claims == null) return null;
        return claimsResolver.apply(claims);
    }

    // Parse claims safely, returning null if invalid
    public Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(getKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();

    }

    public boolean isTokenValid(String token, UserDetails userDetails) {
        Date expiration = extractExpiration(token);
        Date now = new Date(System.currentTimeMillis());
        String email = extractEmail(token);
        return email.equals(userDetails.getUsername()) && expiration.after(now);
    }

    public Set<String> addTokenToBlackList(String token) {
        blacklist_tokens.add(token);
        return blacklist_tokens;
    }

    public boolean isBlacklist(String token) {
        return blacklist_tokens.contains(token);
    }
}
