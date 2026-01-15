"""
Firebase Draft 조회 디버깅
"""

from database import db

print("=" * 60)
print("Firebase Draft 디버깅")
print("=" * 60)

# 1. DB 연결 확인
print(f"\n1. DB 연결: {db.db is not None}")

if not db.db:
    print("❌ Firebase 연결 실패!")
    exit(1)

# 2. Drafts collection 확인
try:
    drafts_ref = db.db.collection('drafts')
    all_docs = list(drafts_ref.limit(5).stream())
    
    print(f"\n2. Drafts Collection:")
    print(f"   - 총 Draft 개수 (첫 5개): {len(all_docs)}")
    
    if all_docs:
        print(f"\n   First Draft 예시:")
        first_draft = all_docs[0].to_dict()
        print(f"   - ID: {all_docs[0].id}")
        print(f"   - Keys: {list(first_draft.keys())}")
        print(f"   - Status: {first_draft.get('status')}")
        print(f"   - Created: {first_draft.get('created_at')}")
    else:
        print("   ❌ Draft가 하나도 없습니다!")
        
except Exception as e:
    print(f"   ❌ Collection 조회 실패: {e}")

# 3. get_pending_email_drafts() 테스트
print(f"\n3. get_pending_email_drafts() 테스트:")
try:
    pending = db.get_pending_email_drafts()
    print(f"   - 반환된 Draft 개수: {len(pending)}")
    
    if pending:
        print(f"\n   First Pending Draft:")
        print(f"   - Keys: {list(pending[0].keys())}")
        print(f"   - Has 'leads': {'leads' in pending[0]}")
        print(f"   - Has 'content': {'content' in pending[0]}")
    else:
        print("   ⚠️ pending draft가 없습니다!")
        
except Exception as e:
    print(f"   ❌ 함수 실행 실패: {e}")
    import traceback
    traceback.print_exc()

# 4. Status별 개수 확인
print(f"\n4. Status별 Draft 개수:")
try:
    statuses = ['pending', 'sent', 'error', 'draft']
    for status in statuses:
        docs = list(db.db.collection('drafts').where('status', '==', status).limit(100).stream())
        print(f"   - {status}: {len(docs)}개")
except Exception as e:
    print(f"   ❌ Status 조회 실패: {e}")

print("\n" + "=" * 60)
print("디버깅 완료")
print("=" * 60)
