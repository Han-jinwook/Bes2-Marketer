
-- 🧨 BRUTAL CLEANUP SCRIPT (Use with Caution!)

-- 1. Drafts 테이블 비우기 (가장 말단 자식)
TRUNCATE TABLE drafts CASCADE;

-- 2. Videos 테이블 비우기 (중간 자식)
TRUNCATE TABLE videos CASCADE;

-- 3. Leads 테이블 비우기 (부모 - 선택사항)
-- 만약 채널 정보(이메일 등)까지 싹 다 날리고 싶다면 아래 주석 해제하세요.
-- TRUNCATE TABLE leads CASCADE;

-- 4. 시퀀스(ID 생성기) 등이 있다면 초기화 (UUID라 필요 없긴 함)
