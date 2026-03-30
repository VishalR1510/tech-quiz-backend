"""Shared dependencies for API routes"""
from fastapi import HTTPException, Depends
from database.supabase import get_supabase, get_supabase_admin


def db_client():
    """Get Supabase client with anon key"""
    client = get_supabase()
    if not client:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return client


def db_admin():
    """Get Supabase admin client with service role key"""
    client = get_supabase_admin()
    if not client:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return client
