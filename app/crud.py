from typing import Sequence, Dict

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import models, schemas
from app.api import weather


class Service:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_cities(self) -> Sequence[models.DBCity]:
        query = select(models.DBCity)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_city(self, city_id: int) -> models.DBCity:
        query = select(models.DBCity).where(
            models.DBCity.id == city_id
        )
        result = await self.session.execute(query)

        return result.scalars().first()

    async def create_city(
            self, city: schemas.CityCreate
    ) -> models.DBCity:
        created_city = models.DBCity(
            name=city.name,
            additional_info=city.additional_info
        )
        self.session.add(created_city)
        await self.session.commit()
        await self.session.refresh(created_city)
        return created_city

    async def update_city(
        self, city_id: int, city: schemas.CityCreate
    ) -> models.DBCity:
        updated_city = await self.get_city(city_id)

        if updated_city:
            updated_city.name = city.name
            updated_city.additional_info = city.additional_info
            await self.session.commit()
            await self.session.refresh(updated_city)
        return updated_city

    async def delete_city(self, city_id: int) -> models.DBCity:
        city = await self.get_city(city_id)

        if city:
            await self.session.delete(city)
            await self.session.commit()
        return city

    async def get_temperatures(
            self, city_id: int = None
    ) -> Sequence[models.DBTemperature]:
        query = select(models.DBTemperature)

        if city_id:
            query = query.where(models.DBTemperature.city_id == city_id)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_temperatures(
            self
    ) -> Dict:
        cities = await self.get_cities()

        async with httpx.AsyncClient() as client:
            for city in cities:
                temperature = await weather.fetch_temperatures(client, city)
                temperature = models.DBTemperature(**temperature.dict())

                self.session.add(temperature)
                await self.session.commit()
                await self.session.refresh(temperature)

        return {
            "detail": "Temperatures successfully updated"
        }
