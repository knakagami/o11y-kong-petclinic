"""
Data provider for interacting with other microservices.
This module handles communication with customers-service and vets-service.
"""

import os
import logging
from typing import List, Optional
import httpx
from app.models import Owner, Vet, Pet, OwnerRequest, PetRequest

logger = logging.getLogger(__name__)


class DataProvider:
    """Provides data access to other microservices"""
    
    def __init__(self):
        self.customers_service_url = os.getenv(
            "CUSTOMERS_SERVICE_URL", 
            "http://customers-service"
        )
        self.vets_service_url = os.getenv(
            "VETS_SERVICE_URL",
            "http://vets-service"
        )
        self.timeout = 30.0
        
    async def get_all_owners(self) -> List[Owner]:
        """
        Fetch all owners from customers-service.
        
        Returns:
            List of Owner objects
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.customers_service_url}/owners")
                response.raise_for_status()
                data = response.json()
                return [Owner(**owner) for owner in data]
        except httpx.HTTPError as e:
            logger.error(f"Error fetching owners: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching owners: {e}")
            raise
    
    async def add_owner(self, owner_request: OwnerRequest) -> Owner:
        """
        Add a new owner to the pet clinic.
        
        Args:
            owner_request: OwnerRequest with owner details
            
        Returns:
            Created Owner object
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.customers_service_url}/owners",
                    json=owner_request.model_dump()
                )
                response.raise_for_status()
                return Owner(**response.json())
        except httpx.HTTPError as e:
            logger.error(f"Error adding owner: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error adding owner: {e}")
            raise
    
    async def add_pet_to_owner(self, owner_id: int, pet_request: PetRequest) -> Pet:
        """
        Add a pet to an existing owner.
        
        Args:
            owner_id: ID of the owner
            pet_request: PetRequest with pet details
            
        Returns:
            Created Pet object
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Convert typeId to type object for API
                pet_data = {
                    "name": pet_request.name,
                    "birthDate": pet_request.birthDate,
                    "type": {
                        "id": pet_request.typeId
                    }
                }
                response = await client.post(
                    f"{self.customers_service_url}/owners/{owner_id}/pets",
                    json=pet_data
                )
                response.raise_for_status()
                return Pet(**response.json())
        except httpx.HTTPError as e:
            logger.error(f"Error adding pet to owner {owner_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error adding pet: {e}")
            raise
    
    async def get_all_vets(self) -> List[Vet]:
        """
        Fetch all veterinarians from vets-service.
        
        Returns:
            List of Vet objects
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.vets_service_url}/vets")
                response.raise_for_status()
                data = response.json()
                return [Vet(**vet) for vet in data]
        except httpx.HTTPError as e:
            logger.error(f"Error fetching vets: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching vets: {e}")
            raise

