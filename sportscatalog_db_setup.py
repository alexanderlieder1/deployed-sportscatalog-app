#!/usr/bin/env python

# Import packages to access and update database
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


# Set up database structure
Base = declarative_base()


# Create User table
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


# Create Category table
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # Serialize data for API endpoint
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


# Create User table
class Item(Base):
    __tablename__ = 'item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # Serialize data for API endpoint
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'title': self.name,
            'description': self.description,
            'id': self.id,
            'cat_id': self.category_id,
        }


# Create database sportscatalog.db
engine = create_engine('sqlite:///sportscatalog.db')
Base.metadata.create_all(engine)
