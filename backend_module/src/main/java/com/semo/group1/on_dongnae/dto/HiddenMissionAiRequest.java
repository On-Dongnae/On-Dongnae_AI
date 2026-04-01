package com.semo.group1.on_dongnae.dto;

import lombok.*;

@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class HiddenMissionAiRequest {
    private String season;
    private String regionType;
    private String weatherSummary;
    private String weeklyCondition;
    private double avgTemp;
    private int rainyDays;
    private int outdoorFriendlyDays;
    private int badAirDays;
    private String missionTitle;
    private String missionDescription;
    private String missionType;
    private boolean isOutdoor;
    private boolean isGroup;
    private int difficulty;
    private int bonusPoints;
}
