from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item, User

engine = create_engine('sqlite:///itemcatalog.db')


Base.metadata.bind = engine


DBSession = sessionmaker(bind=engine)
session = DBSession()

# Users
user1 = User(name="Hamilcar Barca", email="hamilcar.barca275@gmail.com")
session.add(user1)
session.commit()

user2 = User(name="Pyrrhus", email="pyrrhustheepyrian319@gmail.com")
session.add(user2)
session.commit()

# Category soccer
category1 = Category(name="Soccer")
session.add(category1)
session.commit()

item1 = Item(name="Football", description="very round and slippery",
             category=category1, user=user1)
session.add(item1)
session.commit()


# Category Snowboarding
category2 = Category(name="Snowboarding")
session.add(category2)
session.commit()

item1 = Item(name="Goggles", description="very cool", category=category2,
             user=user2)
session.add(item1)
session.commit()

item2 = Item(name="Snowboard", description="long and smooth",
             category=category2, user=user2)
session.add(item2)
session.commit()


# Category Frisbee - empty category
category3 = Category(name="Frisbee")
session.add(category3)
session.commit()


# Category Baseball
category4 = Category(name="Baseball")
session.add(category4)
session.commit()

item1 = Item(name="Shoes",
             description="Lorem ipsum dolor sit amet, felis vitae magna,",
             category=category4,
             user=user1)
session.add(item1)
session.commit()

item2 = Item(name="Bat",
             description="molestie etiam eu eget erat, ipsum amet," +
                         "aenean omnis lacinia viverra arcu ut a" +
                         ". Est aenean vel sagittis elit duis, vulputate " +
                         "praesent maecenas mauris vehicula tristique, " +
                         "dictumst feugiat elementum nec sem, bibendum ",
             category=category4, user=user2)
session.add(item2)
session.commit()

item3 = Item(name="Ball",
             description="non ligula placerat. Maecenas quisque",
             category=category4, user=user2)
session.add(item3)
session.commit()


print "added items!"
