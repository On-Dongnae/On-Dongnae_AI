package com.semo.group1.on_dongnae.controller;

import com.semo.group1.on_dongnae.dto.HiddenMissionAiResponse;
import com.semo.group1.on_dongnae.entity.Mission;
import com.semo.group1.on_dongnae.repository.MissionRepository;
import com.semo.group1.on_dongnae.service.MissionAiService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/ai/missions")
@RequiredArgsConstructor
public class MissionAiController {
    private final MissionRepository missionRepository;
    private final MissionAiService missionAiService;

    @PostMapping("/{missionId}/evaluate")
    public HiddenMissionAiResponse evaluate(@PathVariable Long missionId,
                                            @RequestParam String season,
                                            @RequestParam String regionType,
                                            @RequestParam String weatherSummary,
                                            @RequestParam String weeklyCondition,
                                            @RequestParam double avgTemp,
                                            @RequestParam int rainyDays,
                                            @RequestParam int outdoorFriendlyDays,
                                            @RequestParam int badAirDays) {
        Mission mission = missionRepository.findById(missionId).orElseThrow();
        return missionAiService.evaluateMission(mission, season, regionType, weatherSummary, weeklyCondition,
                avgTemp, rainyDays, outdoorFriendlyDays, badAirDays);
    }
}
