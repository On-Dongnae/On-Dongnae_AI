package com.semo.group1.on_dongnae.controller;

import com.semo.group1.on_dongnae.dto.VerificationAiResponse;
import com.semo.group1.on_dongnae.entity.MissionVerification;
import com.semo.group1.on_dongnae.repository.MissionVerificationRepository;
import com.semo.group1.on_dongnae.service.MissionVerificationAiService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/ai/verifications")
@RequiredArgsConstructor
public class MissionVerificationAiController {
    private final MissionVerificationRepository missionVerificationRepository;
    private final MissionVerificationAiService missionVerificationAiService;

    @PostMapping("/{verificationId}/evaluate")
    public VerificationAiResponse evaluate(@PathVariable Long verificationId) {
        MissionVerification verification = missionVerificationRepository.findById(verificationId).orElseThrow();
        return missionVerificationAiService.evaluateAndAttach(verification, verification.getImages());
    }
}
