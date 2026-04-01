package com.semo.group1.on_dongnae.repository;

import com.semo.group1.on_dongnae.entity.UserMission;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserMissionRepository extends JpaRepository<UserMission, Long> {
    Optional<UserMission> findById(Long id);
}
