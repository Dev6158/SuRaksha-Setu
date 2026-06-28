package com.suraksha.Setu.Config;

import com.suraksha.Setu.Entity.User;
import com.suraksha.Setu.Repo.UserRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
public class DatabaseSeeder implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Value("${DEMO_USER_USERNAME:demo_user}")
    private String demoUsername;

    @Value("${DEMO_USER_PASSWORD:password123}")
    private String demoPassword;

    public DatabaseSeeder(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public void run(String... args) throws Exception {
        if (userRepository.findByUsername(demoUsername).isEmpty()) {
            User demoUser = new User();
            demoUser.setUsername(demoUsername);
            demoUser.setEmail(demoUsername + "@canarabank.co.in");
            demoUser.setPasswordHash(passwordEncoder.encode(demoPassword));
            demoUser.setRoles("ROLE_ADMIN,ROLE_USER");
            demoUser.setEnabled(true);
            userRepository.save(demoUser);
            System.out.println(">>> Database Seeder: Successfully seeded demo user account: " + demoUsername);
        }
    }
}
