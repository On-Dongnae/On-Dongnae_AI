package com.semo.group1.on_dongnae.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.semo.group1.on_dongnae.client.AiServiceClient;
import com.semo.group1.on_dongnae.dto.VerificationAiResponse;
import com.semo.group1.on_dongnae.entity.MissionVerification;
import com.semo.group1.on_dongnae.entity.VerificationImage;
import com.semo.group1.on_dongnae.repository.MissionVerificationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.nio.file.Path;
import java.util.List;

@Service
@RequiredArgsConstructor
public class MissionVerificationAiService {
    private final AiServiceClient aiServiceClient;
    private final MissionVerificationRepository missionVerificationRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public VerificationAiResponse evaluateAndAttach(MissionVerification verification, List<VerificationImage> images) {
        List<Path> imagePaths = images.stream().map(img -> Path.of(img.getImageUrl())).toList();
        VerificationAiResponse response = aiServiceClient.evaluateVerification(
                verification.getUserMission().getMission().getMissionType().name(),
                verification.getContent(),
                imagePaths
        );
        verification.setAiRecommendedStatus(response.getRecommendedStatus());
        try {
            verification.setAiResultJson(objectMapper.writeValueAsString(response));
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
        missionVerificationRepository.save(verification);
        return response;
    }
}
