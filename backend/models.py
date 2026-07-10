from sqlalchemy import Column, Integer, String, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from database import Base

# Association table for materials shared during interactions
interaction_materials = Table(
    'interaction_materials',
    Base.metadata,
    Column('interaction_id', Integer, ForeignKey('interactions.id', ondelete='CASCADE'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True)
)

class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False)
    hospital = Column(String(200), nullable=False)
    email = Column(String(100), unique=True, nullable=False)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="hcp", cascade="all, delete-orphan")

class ProductInfo(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    material_type = Column(String(50), nullable=False)  # 'PDF', 'Sample', 'Brochure'
    stock = Column(Integer, default=0)

    interactions = relationship("Interaction", secondary=interaction_materials, back_populates="materials")

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id", ondelete="CASCADE"), nullable=False)
    date = Column(String(50), nullable=False)  # YYYY-MM-DD
    time = Column(String(50), nullable=False)  # HH:MM
    type = Column(String(50), nullable=False)  # 'Meeting', 'Call', 'Email', 'Conference'
    attendees = Column(String(250), nullable=True)  # Comma-separated names
    topics = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)  # 'Positive', 'Neutral', 'Negative'
    outcomes = Column(Text, nullable=True)
    follow_ups = Column(Text, nullable=True)  # Descriptions of tasks suggested or logged

    hcp = relationship("HCP", back_populates="interactions")
    materials = relationship("ProductInfo", secondary=interaction_materials, back_populates="interactions")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(String(50), nullable=False)  # YYYY-MM-DD
    status = Column(String(50), default="Pending")  # 'Pending', 'Completed'

    hcp = relationship("HCP", back_populates="tasks")
