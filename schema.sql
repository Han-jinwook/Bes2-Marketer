-- =============================================
-- Bes2 Marketer - Supabase Database Schema
-- =============================================
-- 이 SQL을 Supabase Dashboard > SQL Editor에서 실행하세요.

-- 1. leads 테이블: 유튜버 정보
CREATE TABLE IF NOT EXISTS leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    channel_name VARCHAR(255) NOT NULL,
    channel_id VARCHAR(50) UNIQUE NOT NULL,
    subscriber_count INTEGER DEFAULT 0,
    email VARCHAR(255),
    keywords TEXT[], -- 주요 키워드 배열
    channel_url TEXT,
    thumbnail_url TEXT,
    description TEXT,
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'responded', 'converted', 'rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. videos 테이블: 수집된 영상 정보
CREATE TABLE IF NOT EXISTS videos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    video_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    upload_date DATE,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    video_url TEXT,
    thumbnail_url TEXT,
    transcript_text TEXT, -- 자막 전체 텍스트
    summary TEXT, -- AI 요약 내용
    relevance_score FLOAT DEFAULT 0, -- 관련성 점수 (0~1)
    search_keyword VARCHAR(100), -- 검색에 사용된 키워드
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. drafts 테이블: AI 생성 마케팅 초안
CREATE TABLE IF NOT EXISTS drafts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    draft_type VARCHAR(20) NOT NULL CHECK (draft_type IN ('email', 'comment')),
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'sent', 'rejected')),
    tone VARCHAR(50), -- 톤앤매너 (friendly, professional, casual 등)
    language VARCHAR(10) DEFAULT 'ko', -- 언어 코드
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================
-- 인덱스 생성 (검색 성능 최적화)
-- =============================================

-- leads 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_leads_channel_id ON leads(channel_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);

-- videos 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_videos_video_id ON videos(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_lead_id ON videos(lead_id);
CREATE INDEX IF NOT EXISTS idx_videos_upload_date ON videos(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_videos_relevance ON videos(relevance_score DESC);

-- drafts 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_drafts_video_id ON drafts(video_id);
CREATE INDEX IF NOT EXISTS idx_drafts_lead_id ON drafts(lead_id);
CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status);
CREATE INDEX IF NOT EXISTS idx_drafts_type ON drafts(draft_type);

-- =============================================
-- updated_at 자동 업데이트 트리거
-- =============================================

-- 트리거 함수 생성
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 각 테이블에 트리거 적용
DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_videos_updated_at ON videos;
CREATE TRIGGER update_videos_updated_at
    BEFORE UPDATE ON videos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_drafts_updated_at ON drafts;
CREATE TRIGGER update_drafts_updated_at
    BEFORE UPDATE ON drafts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- Row Level Security (RLS) 설정 (선택사항)
-- =============================================
-- 필요시 아래 주석을 해제하여 RLS를 활성화하세요.

-- ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE drafts ENABLE ROW LEVEL SECURITY;

-- =============================================
-- 초기 데이터 확인용 뷰 (선택사항)
-- =============================================

CREATE OR REPLACE VIEW lead_summary AS
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

