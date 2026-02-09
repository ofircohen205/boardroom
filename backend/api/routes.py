from fastapi import APIRouter

from backend.cache import get_cache
from backend.state.enums import Market
from backend.tools.stock_search import StockSuggestion, search_stocks

router = APIRouter(prefix="/api")


@router.get("/markets")
async def get_markets():
    return {m.value: m.name for m in Market}


@router.get("/stocks/search")
async def search_stocks_endpoint(q: str = "", market: str = "US") -> list[dict]:
    """Search for stock symbols matching the query."""
    market_enum = Market.TASE if market == "TASE" else Market.US
    results = await search_stocks(q, market_enum)
    return [
        {
            "symbol": r.symbol,
            "name": r.name,
            "exchange": r.exchange,
        }
        for r in results
    ]


@router.get("/cache/stats")
async def cache_stats():
    return await get_cache().stats()


@router.post("/cache/clear")
async def cache_clear():
    await get_cache().clear()
    return {"status": "cleared"}


# --- Auth ---

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import timedelta

from backend.core.security import create_access_token, get_password_hash, verify_password
from backend.auth.dependencies import get_current_user
from backend.db.models import User, Watchlist, WatchlistItem, Portfolio, Position, AnalysisSession, FinalDecision
from backend.db.database import get_db
from backend.core.settings import settings
from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user_data.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(email=user_data.email, password_hash=hashed_password)
    db.add(new_user)
    
    # Create default watchlist and portfolio
    db.add(Watchlist(user=new_user, name="My Watchlist"))
    db.add(Portfolio(user=new_user, name="My Portfolio"))
    
    await db.commit()
    await db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }


# --- Watchlists ---

class WatchlistItemCreate(BaseModel):
    ticker: str
    market: str = "US"


class WatchlistCreate(BaseModel):
    name: str


@router.get("/watchlists")
async def get_watchlists(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.created_at)
    )
    watchlists = result.scalars().all()
    
    # Eager load items usually handled by relationship, but for simple serialization:
    # We might need a proper Pydantic model for response, but returning dicts for now
    resp = []
    for w in watchlists:
        # Fetch items
        items_res = await db.execute(select(WatchlistItem).where(WatchlistItem.watchlist_id == w.id))
        items = items_res.scalars().all()
        resp.append({
            "id": w.id,
            "name": w.name,
            "items": [{"id": i.id, "ticker": i.ticker, "market": i.market.value} for i in items]
        })
    return resp


@router.post("/watchlists")
async def create_watchlist(
    watchlist: WatchlistCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    new_watchlist = Watchlist(user_id=current_user.id, name=watchlist.name)
    db.add(new_watchlist)
    await db.commit()
    await db.refresh(new_watchlist)
    return {"id": new_watchlist.id, "name": new_watchlist.name, "items": []}


@router.post("/watchlists/{watchlist_id}/items")
async def add_watchlist_item(
    watchlist_id: str,
    item: WatchlistItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    # Verify watchlist ownership
    wl = await db.get(Watchlist, watchlist_id)
    if not wl or wl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
        
    market_enum = Market.TASE if item.market == "TASE" else Market.US
    
    # Check if already exists
    existing = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.watchlist_id == watchlist_id)
        .where(WatchlistItem.ticker == item.ticker)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Ticker already in watchlist")

    new_item = WatchlistItem(
        watchlist_id=watchlist_id,
        ticker=item.ticker,
        market=market_enum
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return {"id": new_item.id, "ticker": new_item.ticker, "market": new_item.market.value}


@router.delete("/watchlists/{watchlist_id}/items/{item_id}")
async def remove_watchlist_item(
    watchlist_id: str,
    item_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    wl = await db.get(Watchlist, watchlist_id)
    if not wl or wl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
        
    item = await db.get(WatchlistItem, item_id)
    if not item or str(item.watchlist_id) != watchlist_id:
        raise HTTPException(status_code=404, detail="Item not found")
        
    await db.delete(item)
    await db.commit()
    return {"status": "deleted"}


# --- Portfolios ---

class PositionCreate(BaseModel):
    ticker: str
    market: str = "US"
    quantity: float
    entry_price: float


class PortfolioCreate(BaseModel):
    name: str

@router.get("/portfolios")
async def get_portfolios(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == current_user.id)
        .order_by(Portfolio.created_at)
    )
    portfolios = result.scalars().all()
    
    resp = []
    for p in portfolios:
        # Fetch positions
        pos_res = await db.execute(select(Position).where(Position.portfolio_id == p.id))
        positions = pos_res.scalars().all()
        resp.append({
            "id": p.id,
            "name": p.name,
            "positions": [
                {
                    "id": pos.id,
                    "ticker": pos.ticker,
                    "quantity": pos.quantity,
                    "avg_entry_price": pos.avg_entry_price,
                    "market": pos.market.value
                } 
                for pos in positions
            ]
        })
    return resp


@router.post("/portfolios")
async def create_portfolio(
    portfolio: PortfolioCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    new_portfolio = Portfolio(user_id=current_user.id, name=portfolio.name)
    db.add(new_portfolio)
    await db.commit()
    await db.refresh(new_portfolio)
    return {"id": new_portfolio.id, "name": new_portfolio.name, "positions": []}


@router.post("/portfolios/{portfolio_id}/positions")
async def add_position(
    portfolio_id: str,
    pos: PositionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    pid = str(portfolio_id) # ensure string
    pf = await db.get(Portfolio, pid)
    if not pf or pf.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    market_enum = Market.TASE if pos.market == "TASE" else Market.US
    
    new_pos = Position(
        portfolio_id=pid,
        ticker=pos.ticker,
        market=market_enum,
        quantity=pos.quantity,
        avg_entry_price=pos.entry_price
    )
    db.add(new_pos)
    await db.commit()
    await db.refresh(new_pos)
    return {
        "id": new_pos.id,
        "ticker": new_pos.ticker,
        "quantity": new_pos.quantity,
        "avg_entry_price": new_pos.avg_entry_price
    }


@router.delete("/portfolios/{portfolio_id}/positions/{position_id}")
async def delete_position(
    portfolio_id: str,
    position_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    pid = str(portfolio_id)
    pf = await db.get(Portfolio, pid)
    if not pf or pf.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    pos = await db.get(Position, position_id)
    if not pos or str(pos.portfolio_id) != pid:
        raise HTTPException(status_code=404, detail="Position not found")
    
    await db.delete(pos)
    await db.commit()
    return {"status": "deleted"}


# --- History ---

@router.get("/analyses")
async def get_analysis_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    ticker: str = None,
    limit: int = 10
):
    query = select(AnalysisSession).where(AnalysisSession.user_id == current_user.id)
    
    if ticker:
        query = query.where(AnalysisSession.ticker == ticker)
        
    query = query.order_by(desc(AnalysisSession.created_at)).limit(limit)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    resp = []
    for s in sessions:
        # Load final decision if exists
        # In async sqlalchemy we might need explicit load or check relationship
        # Assuming eager load or separate fetch. Let's separate fetch for safety in this snippet
        fd_res = await db.execute(select(FinalDecision).where(FinalDecision.session_id == s.id))
        fd = fd_res.scalars().first()
        
        resp.append({
            "id": s.id,
            "ticker": s.ticker,
            "market": s.market.value,
            "created_at": s.created_at,
            "decision": fd.action.value if fd else None,
            "confidence": fd.confidence if fd else None
        })
    return resp


