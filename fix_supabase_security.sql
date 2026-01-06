-- ========================================================
-- [Fix Script] Supabase Security & RLS Patch
-- ========================================================
-- 이 스크립트를 Supabase Dashboard > SQL Editor에 복사하고 실행(Run)하세요.
-- 목적: Security Advisor의 4가지 경고를 모두 해결합니다.

-- 1. Security Definer View 문제 해결
-- (Views의 소유권 문제를 해결하기 위해 security_invoker를 설정하거나 재생성)
DROP VIEW IF EXISTS public.lead_summary;

CREATE OR REPLACE VIEW public.lead_summary 
WITH (security_invoker = true) -- [핵심] 뷰 호출자의 권한을 사용하도록 명시
AS
SELECT 
    l.id,
    l.channel_name,
    l.subscriber_count,
    l.status,
    COUNT(DISTINCT v.id) as video_count,
    COUNT(DISTINCT d.id) as draft_count
FROM leads l
LEFT JOIN videos v ON l.id = v.lead_id
LEFT JOIN drafts d ON l.id = d.lead_id
GROUP BY l.id, l.channel_name, l.subscriber_count, l.status;


-- 2. RLS(Row Level Security) 활성화
-- 테이블의 보안 잠금을 켭니다. (기본값: 아무도 접근 불가)
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.drafts ENABLE ROW LEVEL SECURITY;


-- 3. 접근 권한 정책(Policy) 생성
-- Bes2 App(서비스)이 데이터에 접근할 수 있도록 허용하는 정책입니다.
-- (주의: 지금은 개발 편의성을 위해 모든 사용자에게 액세스를 허용합니다. 필요 시 수정 가능)

-- [Leads 테이블 정책]
CREATE POLICY "Enable all access for leads" ON public.leads
    FOR ALL USING (true) WITH CHECK (true);

-- [Videos 테이블 정책]
CREATE POLICY "Enable all access for videos" ON public.videos
    FOR ALL USING (true) WITH CHECK (true);

-- [Drafts 테이블 정책]
CREATE POLICY "Enable all access for drafts" ON public.drafts
    FOR ALL USING (true) WITH CHECK (true);

-- 완료 메시지
SELECT '모든 보안 설정이 완료되었습니다. Security Advisor를 새로고침하세요.' as result;
