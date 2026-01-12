
-- ⚠️ WARNING: This will delete ALL videos and drafts!
-- Preserves 'leads' (channel info/emails) for future use.

-- 1. Delete all drafts first (due to Foreign Key dependency)
DELETE FROM drafts;

-- 2. Delete all videos
DELETE FROM videos;

-- 3. (Optional) Uncomment below if you want to wipe collected channels/emails too
-- DELETE FROM leads;
