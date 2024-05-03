package com.osiris.backend.security.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.osiris.backend.model.User;
import com.osiris.backend.repository.UserRepository;
import com.osiris.backend.security.service.impl.UserDetailsImpl;

@Service
public class UserDetailsServiceImpl implements UserDetailsService {
    @Autowired
    UserRepository userRepository;

    @Override
    @Transactional
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
      User user = userRepository.findByUsername(username)
          .orElseThrow(() -> new UsernameNotFoundException("User Not Found with username: " + username));

      return UserDetailsImpl.build(user);
    }

  }
