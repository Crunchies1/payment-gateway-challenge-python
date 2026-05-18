from pydantic import BaseModel, Field
from typing import Optional
import uuid

class Card(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    number: str         # Would probably have an index here
    expiry_month: int   # Probably no index, full table scan after tracking down number should be relatively small
    expiry_year: int    # No index again, for same reason as row above

    def last_four_digits(self):
        return self.number[-4:]

class CardRepository:
    def __init__(self):
        self._store: dict[str, Card] = {}

    def create(self, card: Card) -> None:
        self._store[card.id] = card

    def get(self, id) -> Optional[Card]:
        return self._store.get(id)
    
    def get_by_card_details(self, number: str, expiry_month: int, expiry_year: int) -> Optional[Card]:
        # Didn't implement efficient algorithm here, please assume this will be handled
        # by DB level operations   :'(
        for card in self._store.values():
            if not (card.number == number and card.expiry_month == expiry_month and card.expiry_year == expiry_year):
                continue
            return card
        return None
    
card_repo = CardRepository()