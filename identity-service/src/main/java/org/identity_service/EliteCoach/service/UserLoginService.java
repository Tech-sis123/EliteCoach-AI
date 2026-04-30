package org.identity_service.EliteCoach.service;

import org.identity_service.EliteCoach.handler.exceptions.UserNotFoundException;
import org.identity_service.EliteCoach.model.User;
import org.identity_service.EliteCoach.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class UserLoginService {

    private final Map<String, User> dbCache;

    @Autowired
    private UserRepository userRepository;

    public UserLoginService() {
        dbCache = new ConcurrentHashMap<>();
    }

    public User getUser(String email) {
        if(dbCache.containsKey(email)) {
            return dbCache.get(email);
        } else {
            User user = userRepository.
                    findByEmail(email).orElseThrow(() -> new
                            UserNotFoundException("User not found"));
            dbCache.put(email, user);
            return user;
        }
    }
}
