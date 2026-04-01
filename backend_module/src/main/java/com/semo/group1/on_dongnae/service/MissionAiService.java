package com.semo.group1.on_dongnae.service;

import com.semo.group1.on_dongnae.client.AiServiceClient;
import com.semo.group1.on_dongnae.dto.HiddenMissionAiRequest;
import com.semo.group1.on_dongnae.dto.HiddenMissionAiResponse;
import com.semo.group1.on_dongnae.entity.Mission;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class MissionAiService {
    private final AiServiceClient aiServiceClient;

    public HiddenMissionAiResponse evaluateMission(Mission mission, String season, String regionType, String weatherSummary, String weeklyCondition,
                                                  double avgTemp, int rainyDays, int outdoorFriendlyDays, int badAirDays) {
        HiddenMissionAiRequest request = HiddenMissionAiRequest.builder()
                .season(season)
                .regionType(regionType)
                .weatherSummary(weatherSummary)
                .weeklyCondition(weeklyCondition)
                .avgTemp(avgTemp)
                .rainyDays(rainyDays)
                .outdoorFriendlyDays(outdoorFriendlyDays)
                .badAirDays(badAirDays)
                .missionTitle(mission.getTitle())
                .missionDescription(mission.getDescription())
                .missionType(mission.getMissionType().name())
                .isOutdoor(mission.getIsOutdoor())
                .isGroup(mission.getIsGroup())
                .difficulty(mission.getDifficulty())
                .bonusPoints(mission.getBonusPoints())
                .build();
        return aiServiceClient.evaluateHiddenMission(request);
    }
}
