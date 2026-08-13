from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime

class Apartment(Base):
    __tablename__ = 'apartments'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price_per_hour = Column(Float, nullable=False)
    price_per_day = Column(Float, nullable=False)
    photo_file_id = Column(String, nullable=False)  # file_id от Telegram
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    apartment_id = Column(Integer, ForeignKey('apartments.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_confirmed = Column(Boolean, default=False)
    contract_signed = Column(Boolean, default=False)
    user = relationship("User", backref="bookings")
    apartment = relationship("Apartment", backref="bookings")
