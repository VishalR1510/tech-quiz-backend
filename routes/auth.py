from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.supabase import get_supabase_admin

router = APIRouter(tags=["Auth"])

class ResolveEmailRequest(BaseModel):
    identifier: str

@router.post("/auth/resolve-email")
async def resolve_email(req: ResolveEmailRequest):
    identifier = req.identifier
    
    # If it's already an email, just return it
    if "@" in identifier:
        return {"email": identifier}
    
    # Otherwise, it's a Name. We need to find the user in Supabase Auth via Admin Client
    admin_client = get_supabase_admin()
    if not admin_client:
        raise HTTPException(status_code=500, detail="Admin client not configured")
        
    try:
        # Note: In a large production app, iterating over all users is slow, but for this project it works perfectly without extra tables.
        # Fetch up to 1000 users. If you have more, you would need pagination.
        response = admin_client.auth.admin.list_users()
        users = getattr(response, 'users', response)
        
        for user in users:
            # Depending on python client version, metadata might be in user_metadata or raw_user_meta_data
            metadata = getattr(user, "user_metadata", None) or getattr(user, "raw_user_meta_data", {}) or {}
            
            # Check if the name in metadata matches the requested identifier (case-insensitive)
            if metadata.get("name", "").lower() == identifier.lower():
                return {"email": user.email}
                
        raise HTTPException(status_code=404, detail="No user found with that Name.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error resolving email: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while resolving username.")
