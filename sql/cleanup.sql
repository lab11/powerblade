
SELECT TABLE_NAME 
FROM information_schema.tables 
WHERE TABLE_TYPE LIKE 'BASE TABLE'
and TABLE_SCHEMA='powerblade'
order by TABLE_NAME asc;

SELECT TABLE_NAME 
FROM information_schema.tables 
WHERE TABLE_TYPE LIKE 'VIEW'
and TABLE_SCHEMA='powerblade'
order by TABLE_NAME asc;

drop table calendar;

drop table inf_blees_light_lookup;

drop view days_w_resets;

rename table avgPower to old_avgPower;

rename table temp_powerblade to seq_powerblade;

rename table instpower to old_instpower;
rename table maxPower to old_maxPower;
rename table overall_power_filled to old_overall_power_filled;

rename table ss_data to loc1_data;
rename table ss_powerblade to loc1_dat_powerblade;
rename table ss_power_states to loc1_ss_power_states;
rename table inf_ss_pb_lookup to loc1_pb_lookup;

rename table upd_blees_binary to old_upd_blees_binary;
rename table upd_blees_power to old_upd_blees_power;
rename table upd_overall_power to old_upd_overall_power;
rename table upd_overall_power_shortmac to old_upd_overall_power_shortmac;
rename table upd_recent_power to old_upd_recent_power;