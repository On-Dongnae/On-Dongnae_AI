import os, random, csv
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
HM = os.path.join(BASE_DIR,'data','hidden_mission','hidden_mission_candidates.csv')
VD = os.path.join(BASE_DIR,'data','verification','verification_final_decision.csv')
random.seed(42)
seasons=['spring','summer','fall','winter']
regions=['residential','park_area','school_area']
weekly_conditions=['outdoor_good','indoor_preferred','mixed','hot_week','cold_week']
mission_types=['group_cleanup','recycling','kindness_activity','energy_saving','jogging_group']
with open(HM,'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['candidate_id','week_id','season','region_type','weather_summary','weekly_condition','avg_temp','rainy_days','outdoor_friendly_days','bad_air_days','mission_title','mission_description','mission_type','is_outdoor','is_group','difficulty','bonus_points','novelty_score','safety_score','feasibility_score','participation_score','overall_score','approve_label'])
    for i in range(200):
        s=random.choice(seasons); r=random.choice(regions); wc=random.choice(weekly_conditions); mt=random.choice(mission_types)
        outdoor = mt in ['group_cleanup','jogging_group'] and wc!='indoor_preferred'
        group = mt in ['group_cleanup','jogging_group']
        diff=random.randint(1,4); bonus=random.choice([50,70,80,100])
        novelty=random.randint(2,5); safety=5 if wc!='hot_week' else random.randint(2,4); feas=5 if wc in ['outdoor_good','mixed'] or not outdoor else random.randint(2,4)
        part=random.randint(2,5); overall=round((novelty+safety+feas+part)/4)
        approve=1 if overall>=4 and safety>=3 else 0
        w.writerow([f'c{i}',f'2026-W{(i%12)+1}',s,r,f'{wc} weather',wc,random.uniform(-2,30),random.randint(0,4),random.randint(1,6),random.randint(0,3),f'{mt} mission {i}',f'Description for {mt} {i}',mt,int(outdoor),int(group),diff,bonus,novelty,safety,feas,part,overall,approve])
with open(VD,'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['sample_id','mission_type','description_text','clip_match_score','predicted_activity_class','activity_class_confidence','person_count_pred','trash_bag_detected','recyclable_item_detected','recycle_bin_detected','litter_picker_detected','image_quality_score','text_length','mission_match_flag','final_label'])
    labels=['approved','needs_review','rejected']
    for i in range(200):
        mt=random.choice(mission_types)
        clip=round(random.uniform(0.1,0.95),4)
        pred=mt if random.random()>0.2 else random.choice(mission_types)
        conf=round(random.uniform(0.3,0.99),4)
        pc=random.randint(0,5)
        tb=random.randint(0,1); ri=random.randint(0,1); rb=random.randint(0,1); lp=random.randint(0,1)
        iq=round(random.uniform(0.2,0.95),4); tl=random.randint(5,80); mm=1 if pred==mt else 0
        score=clip*0.45+iq*0.15+(0.1 if tl>=10 else 0)+(0.15 if mt=='group_cleanup' and pc>=2 else 0)+(0.15 if mt=='group_cleanup' and (tb or rb) else 0)
        if mt=='recycling' and (ri or rb): score +=0.2
        if mt=='jogging_group' and pc>=2: score +=0.2
        if score>=0.75: label='approved'
        elif score>=0.5: label='needs_review'
        else: label='rejected'
        w.writerow([f's{i}',mt,f'{mt} description {i}',clip,pred,conf,pc,tb,ri,rb,lp,iq,tl,mm,label])
print('seed data generated')
