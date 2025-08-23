tests/test_contradictions.py
import pytest
from src.db.session import SessionLocal
from src.db.models import Belief

@pytest.mark.asyncio
async def test_reflection_updates_beliefs(monkeypatch):
    from src.core.consistency import reflect_beliefs
    with SessionLocal() as db:
        db.add(Belief(subject="Sky", predicate="color", object="blue", confidence=0.8, source_id="test"))
        db.add(Belief(subject="Sky", predicate="color", object="green", confidence=0.7, source_id="test"))
        db.commit()

        async def fake_detect(facts):
            return {"updates":[{"subject":"Sky","predicate":"color","object":"blue","confidence":0.95}]}
        from src.llm import provider
        monkeypatch.setattr(provider.LLM, "detect_contradictions", lambda self, facts: fake_detect(facts))

        await reflect_beliefs(db)
        q = db.query(Belief).filter(Belief.subject=="Sky", Belief.predicate=="color").all()
        assert any(b.object=="blue" and b.confidence>=0.9 for b in q)