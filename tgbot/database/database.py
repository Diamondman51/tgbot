import asyncio
from sqlalchemy import ForeignKey, exists, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session, sessionmaker


engine = create_async_engine(url="sqlite+aiosqlite:///bot.db",)

session = async_sessionmaker(bind=engine)
# session = AsyncSession(bind=engine)
# session = Session(bind=engine)
# session = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    tg_user_id: Mapped[int] = mapped_column(unique=True)
    notion_db_token: Mapped[str] = mapped_column(nullable=True)
    notion_db_id: Mapped[str] = mapped_column(nullable=True)
    links: Mapped[list['Links']] = relationship(uselist=True, back_populates='user')


class Links(Base):
    __tablename__ = 'links'
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, unique=True)
    user: Mapped[User] = relationship(uselist=False, back_populates="links")
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_user_id', ondelete='cascade'))
    url: Mapped[str]
    title: Mapped[str]
    category: Mapped[str]
    priority: Mapped[str]


async def main():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(Base.metadata.drop_all)

    
async def test():
    async with session.begin() as conn:
        user = select(User).filter(User.tg_user_id == 1)
        res = await conn.execute(user)
        e = select(exists().where(User.tg_user_id == 12))
        print(res.scalar_one_or_none())
        res = await conn.execute(e)
        print(res.scalar())


if __name__ == '__main__':
    # asyncio.run(main())
    # asyncio.run(test())
    

    pass
