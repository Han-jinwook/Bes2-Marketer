-- ========================================================
-- [Feature Add] App Settings Table (키워드 저장용)
-- ========================================================
-- 이 스크립트를 Supabase SQL Editor에서 실행하세요.

-- 1. app_settings 테이블 생성
CREATE TABLE IF NOT EXISTS app_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL, -- 설정 키 (예: 'search_keywords')
    value TEXT NOT NULL, -- 설정 값 (JSON 또는 텍스트)
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. RLS(보안) 및 권한 설정
ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all access for app_settings" ON app_settings
    FOR ALL USING (true) WITH CHECK (true);

-- 3. 초기 데이터 삽입 (기본 키워드)
INSERT INTO app_settings (key, value)
VALUES ('search_keywords', '사진 정리, 갤러리 정리, 용량 부족, 구글포토 백업')
ON CONFLICT (key) DO NOTHING;

SELECT '설정 테이블 생성 및 초기화 완료!' as result;
