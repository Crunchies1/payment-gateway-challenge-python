"""Cards Service"""

from pydantic import BaseModel
from ..models import cards
from typing import Optional

class CardRequest(BaseModel):
    number: str
    expiry_month: int
    expiry_year: int

def get_or_create_card(req: CardRequest) -> cards.Card:
    # Get card by details, early return if found
    card: Optional[cards.Card] = cards.card_repo.get_by_card_details(
        number=req.number,
        expiry_month=req.expiry_month,
        expiry_year=req.expiry_year
    )
    if card:
        return card
    
    # Create new card, return newly created card
    new_card: cards.Card = cards.Card(
        number=req.number,
        expiry_month=req.expiry_month,
        expiry_year=req.expiry_year
    )
    cards.card_repo.create(card=new_card)
    return new_card

def get_by_id(card_id: str) -> Optional[cards.Card]:
    return cards.card_repo.get(card_id)