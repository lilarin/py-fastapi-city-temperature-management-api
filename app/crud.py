from typing import Sequence, Dict

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import models, schemas
from app.api import weather


class Service:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_cities(self) -> Sequence[models.City]:
        query = select(models.City)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_city(self, city_id: int) -> models.City:
        query = select(models.City).where(
            models.City.id == city_id
        )
        result = await self.session.execute(query)

        return result.scalars().first()

    async def create_city(
            self, city: schemas.CityCreate
    ) -> models.City:
        created_city = models.City(
            name=city.name,
            additional_info=city.additional_info
        )
        self.session.add(created_city)
        await self.session.commit()
        await self.session.refresh(created_city)
        return created_city

    async def update_city(
        self, city_id: int, city: schemas.CityCreate
    ) -> models.City:
        updated_city = await self.get_city(city_id)

        if updated_city:
            updated_city.name = city.name
            updated_city.additional_info = city.additional_info
            await self.session.commit()
            await self.session.refresh(updated_city)
        return updated_city

    async def delete_city(self, city_id: int) -> models.City:

        city = await self.get_city(city_id)

        if city:
            await self.session.delete(city)
            await self.session.commit()
        return city

    async def get_temperatures(
            self, city_id: int = None
    ) -> Sequence[models.Temperature]:
        query = select(models.Temperature)

        if city_id:
            query = query.where(models.Temperature.city_id == city_id)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_temperatures(
            self
    ) -> Dict:
        cities = await self.get_cities()

        async with httpx.AsyncClient() as client:
            for city in cities:
                temperature = await weather.fetch_temperatures(client, city)
                temperature = models.Temperature(**temperature.dict())

                self.session.add(temperature)
                await self.session.commit()
                await self.session.refresh(temperature)

        return {
            "detail": "Temperatures successfully updated"
        }
