package com.semo.group1.on_dongnae.client;

import com.semo.group1.on_dongnae.dto.HiddenMissionAiRequest;
import com.semo.group1.on_dongnae.dto.HiddenMissionAiResponse;
import com.semo.group1.on_dongnae.dto.VerificationAiResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import java.nio.file.Path;
import java.util.List;

@Component
public class AiServiceClient {
    private final WebClient webClient;

    public AiServiceClient(@Value("${ai.service.base-url:http://localhost:8010}") String baseUrl) {
        this.webClient = WebClient.builder().baseUrl(baseUrl).build();
    }

    public HiddenMissionAiResponse evaluateHiddenMission(HiddenMissionAiRequest request) {
        return webClient.post()
                .uri("/predict/hidden-mission")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(HiddenMissionAiResponse.class)
                .block();
    }

    public VerificationAiResponse evaluateVerification(String missionType, String descriptionText, List<Path> imagePaths) {
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("mission_type", missionType);
        body.add("description_text", descriptionText);
        imagePaths.forEach(path -> body.add("files", new FileSystemResource(path)));

        return webClient.post()
                .uri("/predict/verification-from-images")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(body))
                .retrieve()
                .bodyToMono(VerificationAiResponse.class)
                .block();
    }
}
