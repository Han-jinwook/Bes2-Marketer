-- ========================================================
-- [Fix Script] Supabase Function Search Path Warning Fix
-- ========================================================
-- 이 스크립트를 Supabase Dashboard > SQL Editor에 복사하고 실행(Run)하세요.
-- 목적: Security Advisor의 'Function Search Path Mutable' 경고 해결

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER 
LANGUAGE plpgsql
-- [핵심] search_path를 명시적으로 설정하여 보안 강화
SET search_path = public
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

SELECT '함수 보안 패치가 완료되었습니다. Warning이 사라졌는지 확인하세요.' as result;
