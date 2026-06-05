from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.research_repository import ResearchRepository


async def get_research_repo(db: AsyncSession = Depends(get_db)) -> ResearchRepository:
    return ResearchRepository(db)
