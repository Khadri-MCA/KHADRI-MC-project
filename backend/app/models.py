from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Date, Time, DateTime, Boolean, ForeignKey
)
from sqlalchemy.orm import relationship

from app.database import Base


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    specialty = Column(String(120))
    hospital = Column(String(180))
    email = Column(String(150))
    phone = Column(String(30))
    tier = Column(String(20), default="B")
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp")


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(180), nullable=False)
    type = Column(String(40), nullable=False)
    sku = Column(String(60))
    is_sample = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)
    rep_id = Column(Integer, nullable=False, default=1)
    interaction_type = Column(String(30), nullable=False)
    interaction_date = Column(Date, nullable=False)
    interaction_time = Column(Time)
    attendees = Column(Text)
    topics_discussed = Column(Text)
    sentiment = Column(String(20))
    outcomes = Column(Text)
    follow_up_actions = Column(Text)
    ai_summary = Column(Text)
    raw_source = Column(String(20), default="form")
    raw_transcript = Column(Text)
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")


class InteractionMaterial(Base):
    __tablename__ = "interaction_materials"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Integer, default=1)


class InteractionAuditLog(Base):
    __tablename__ = "interaction_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(30), nullable=False)
    tool_used = Column(String(60))
    diff = Column(Text)
    performed_at = Column(DateTime, default=datetime.utcnow)
