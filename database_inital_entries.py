#!/usr/bin/env python

# Import packages to access and update database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sportscatalog_db_setup import Base, Category, Item, User


# Connect to Database and create database session
engine = create_engine('sqlite:///sportscatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create dummy user
User1 = User(name="John Doe", email="john@doe.com")
session.add(User1)
session.commit()


# Items for Football
category1 = Category(user_id=1, name="Football")
session.add(category1)
session.commit()

# Create item 1 for Football Category
item1 = Item(user_id=1, name="Jersey",
             description="A jersey specifically designed to identify a team",
             category=category1)
session.add(item1)
session.commit()

# Create item 2 for Football Category
item2 = Item(user_id=1, name="Football stadium",
             description="Venue where a football match takes place",
             category=category1)
session.add(item2)
session.commit()

# Create item 3 for Football Category
item3 = Item(user_id=1, name="Champions Leaugue",
             description="Championship organized by UEFA",
             category=category1)
session.add(item3)
session.commit()

# Create item 4 for Football Category
item4 = Item(user_id=1, name="World Cup",
             description="World competition that takes place every 4 years",
             category=category1)
session.add(item4)
session.commit()

# Create item 5 for Football Category
item5 = Item(user_id=1, name="Football boots",
             description="Specific football boots to improve player's balance",
             category=category1)
session.add(item5)
session.commit()

# Create item 6 for Football Category
item6 = Item(user_id=1, name="European Cup",
             description="European competition that takes place every 4 years",
             category=category1)
session.add(item6)
session.commit()


# Items for Basketball
category2 = Category(user_id=1, name="Basketball")
session.add(category2)
session.commit()

# Create item 1 for Basketball Category
item1 = Item(user_id=1, name="LA Lakers",
             description="Basketball club from Los Angeles",
             category=category2)
session.add(item1)
session.commit()

# Create item 2 for Basketball Category
item2 = Item(user_id=1, name="Michael Jordan",
             description="Famous basketball player",
             category=category2)
session.add(item2)
session.commit()

# Create item 3 for Basketball Category
item3 = Item(user_id=1, name="Chicago Bulls",
             description="Basketball club from Chicago",
             category=category2)
session.add(item3)
session.commit()

# Create item 4 for Basketball Category
item4 = Item(user_id=1, name="LeBron James",
             description="Famous basketball player (#2)",
             category=category2)
session.add(item4)
session.commit()

# Create item 5 for Basketball Category
item5 = Item(user_id=1, name="Dallas Mavericks",
             description="Basketball club from Dallas",
             category=category2)
session.add(item5)
session.commit()


# Print confirmation for successful data entries
print("Initial db entries added")
