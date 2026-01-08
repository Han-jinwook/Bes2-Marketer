# Current Status & Known Issues (Session Transfer)

## 🚨 Critical Issues
1.  **DB Create Failure (Silent)**:
    - The application reports "Analysis Complete" and success balloons appear, but **NO data is actually saved to the `drafts` table**.
    - Debugging confirmed `Total rows fetched: 0` in `drafts`.
    - This creates a critical disconnect: Users spend tokens on analysis, but the result evaporates.

2.  **Email Management Tab Empty**:
    - Consequence of Issue #1. Since no drafts are saved, the "Pending Emails" list is persistently empty (or misleadingly missing items).
    - The recent fix to query logic (`*, videos(*), leads(*)`) is likely correct, but futile because the table itself is empty.

## 🛠️ Recent Changes (v2.3)
- **Deep Scan**: Added logic to scan latest 5 videos for emails.
- **UI Improvements**:
    - Removed "Select All" external checkbox, made list items selected by default.
    - Added "Select All/Deselect All" text button.
    - Removed "Thumbnail" column from display for performance.
    - Added "Select Delete" button.
    - Added "Manual Email Input" in the Email Management tab.
- **Database**:
    - Added `app_settings` table for keyword persistence.
    - Attempted to persist keywords to DB (working).

## 📝 Next Steps for New Session
1.  **Debug INSERT Operation**:
    - Isolate `db.create_lead`, `db.create_video`, `db.create_draft`.
    - Check for **Foreign Key Constraint** violations (e.g., is `lead_id` correctly returned and passed?).
    - Check for **RLS Policy** blocking INSERTs (Supabase might reject writes if policy isn't `true` for anon/service_role).
2.  **Fix Error Handling**:
    - `main.py` needs better exception catching around the DB insert block to show *real* SQL errors to the user instead of passing silently.
3.  **Verify Data Flow**:
    - Ensure `video["channel_id"]` -> `leads` creation -> returns `lead_id` -> used in `videos` & `drafts` creation sequence is unbreakable.
