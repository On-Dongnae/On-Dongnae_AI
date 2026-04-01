package com.semo.group1.on_dongnae.dto;

import lombok.*;
import java.util.List;
import java.util.Map;

@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class VerificationAiResponse {
    private String missionType;
    private double clipMatchScore;
    private String bestMatchingPrompt;
    private int personCount;
    private List<String> detectedClasses;
    private Map<String, Integer> objectPresence;
    private double imageQualityScore;
    private int textLength;
    private String recommendedStatus;
    private double confidenceScore;
    private Map<String, Double> classProbabilities;
}
