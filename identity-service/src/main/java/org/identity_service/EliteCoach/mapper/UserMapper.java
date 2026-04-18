package org.identity_service.EliteCoach.mapper;

import org.identity_service.EliteCoach.model.User;
import org.identity_service.EliteCoach.dto.UserRequest;
import org.modelmapper.ModelMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Objects;

@Service
public class UserMapper {

    @Autowired
    private ModelMapper mapper;


    public User convertToModel(UserRequest userRequest) {
        if(!Objects.isNull(userRequest))
            return mapper.map(userRequest,User.class);
        else
            throw new RuntimeException("Invalid user details");
    }

    public UserRequest convertToRequest(User user) {
        if(!Objects.isNull(user))
            return mapper.map(user,UserRequest.class);
        else
            throw new RuntimeException("Invalid user details");
    }
}
