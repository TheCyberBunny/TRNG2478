--Robopulse Command Center - Day 2 Phase B challenge answer key
--Answering Business question #2 with SQL
--\i challenge_query.sql

--step1 start from the missions table
--step2 JOIN robots to answer the question "where is the assigned robot stationed?"
--step3 JOIN operators to answer the question "where is the assigned operator stationed?"
--step4 WHERE the two facility_id values disagree

SELECT
    m.id AS mission_id,
    m.title,
    r.facility_id AS robot_facility_id,
    o.facility_id AS operator_facility_id
FROM missions m
JOIN robots r ON r.id = m.robot_id
JOIN operators o ON o.id = m.operator_id
WHERE r.facility_id != o.facility_id;