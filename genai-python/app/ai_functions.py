"""
AI Functions (Tools) for LangChain Agent.
These functions are callable by the LLM to perform actions.
"""

import logging
import json
from typing import List
from langchain.tools import tool

from app.data_provider import DataProvider
from app.vector_store import VectorStoreController
from app.models import OwnerRequest, PetRequest

logger = logging.getLogger(__name__)


class AIFunctions:
    """Container for AI functions that can be called by the LLM"""
    
    def __init__(self, data_provider: DataProvider, vector_store_controller: VectorStoreController):
        self.data_provider = data_provider
        self.vector_store_controller = vector_store_controller
        
    def get_tools(self):
        """
        Get all available tools for the LangChain agent.
        
        Returns:
            List of LangChain tools
        """
        
        @tool
        async def list_owners() -> str:
            """
            List all the owners that the pet clinic has.
            Use this when the user asks about owners, their information, or wants to see all owners.
            
            Returns:
                JSON string containing list of owners with their pets
            """
            try:
                owners = await self.data_provider.get_all_owners()
                owners_list = [owner.model_dump() for owner in owners]
                return json.dumps({"owners": owners_list}, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error in list_owners: {e}")
                return json.dumps({"error": str(e)})
        
        @tool
        async def add_owner_to_petclinic(
            firstName: str,
            lastName: str,
            address: str,
            city: str,
            telephone: str
        ) -> str:
            """
            Add a new pet owner to the pet clinic.
            The owner must include a first name and last name as two separate words,
            plus an address, city, and a 10-digit phone number.
            
            Args:
                firstName: Owner's first name
                lastName: Owner's last name
                address: Owner's street address
                city: Owner's city
                telephone: Owner's 10-digit phone number
                
            Returns:
                JSON string containing the created owner information
            """
            try:
                owner_request = OwnerRequest(
                    firstName=firstName,
                    lastName=lastName,
                    address=address,
                    city=city,
                    telephone=telephone
                )
                owner = await self.data_provider.add_owner(owner_request)
                return json.dumps({"owner": owner.model_dump()}, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error in add_owner_to_petclinic: {e}")
                return json.dumps({"error": str(e)})
        
        @tool
        def list_vets(query: str = "") -> str:
            """
            List the veterinarians that the pet clinic has.
            Use this when the user asks about vets, veterinarians, or their specialties.
            You can provide a query to search for specific vets or specialties.
            
            Args:
                query: Optional search query (e.g., vet name, specialty like "radiology" or "surgery")
                
            Returns:
                JSON string containing list of matching veterinarians
            """
            try:
                # If no query provided, search with generic term to get top results
                search_query = query if query else "veterinarian"
                
                # Determine top_k based on query
                top_k = 50 if not query else 20
                
                results = self.vector_store_controller.search_vets(search_query, top_k=top_k)
                
                return json.dumps({"vets": results}, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error in list_vets: {e}")
                return json.dumps({"error": str(e)})
        
        @tool
        async def add_pet_to_owner(
            ownerId: int,
            petName: str,
            birthDate: str,
            petTypeId: int
        ) -> str:
            """
            Add a pet with the specified petTypeId to an owner identified by ownerId.
            
            The allowed Pet type IDs are:
            - 1: cat
            - 2: dog
            - 3: lizard
            - 4: snake
            - 5: bird
            - 6: hamster
            
            Args:
                ownerId: ID of the owner to add the pet to
                petName: Name of the pet
                birthDate: Birth date of the pet in format YYYY-MM-DD
                petTypeId: Pet type ID (1-6)
                
            Returns:
                JSON string containing the created pet information
            """
            try:
                # Validate pet type ID
                if petTypeId not in [1, 2, 3, 4, 5, 6]:
                    return json.dumps({
                        "error": "Invalid pet type ID. Must be 1-6 (cat, dog, lizard, snake, bird, hamster)"
                    })
                
                pet_request = PetRequest(
                    name=petName,
                    birthDate=birthDate,
                    typeId=petTypeId
                )
                
                pet = await self.data_provider.add_pet_to_owner(ownerId, pet_request)
                return json.dumps({"pet": pet.model_dump()}, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error in add_pet_to_owner: {e}")
                return json.dumps({"error": str(e)})
        
        # Return all tools
        return [
            list_owners,
            add_owner_to_petclinic,
            list_vets,
            add_pet_to_owner
        ]

