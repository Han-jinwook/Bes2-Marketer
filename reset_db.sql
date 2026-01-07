-- ========================================================
-- [Clean Reset Script] DB 완전 초기화
-- ========================================================
-- 이 스크립트를 Supabase SQL Editor에서 실행하면
-- 모든 데이터가 영구적으로 삭제됩니다. (복구 불가)

-- 1. 데이터 비우기 (TRUNCATE)
-- CASCADE 옵션: leads(채널)를 지우면, 거기에 딸린 videos, drafts도 자동으로 같이 지워짐
TRUNCATE TABLE leads, videos, drafts CASCADE;

-- 2. 시퀀스(ID 생성기) 초기화 (선택 사항)
-- UUID를 쓰므로 굳이 필요 없지만, 깔끔하게 정리

SELECT '모든 데이터가 깨끗하게 삭제되었습니다. 이제 새로운 사냥을 시작하세요!' as result;
