"""
Pydantic models for GenAI Python Service.
These models match the DTOs used in the Spring Java version.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PetType(BaseModel):
    """Pet type model"""
    id: int
    name: str


class Pet(BaseModel):
    """Pet model"""
    id: Optional[int] = None
    name: str
    birthDate: str
    type: PetType


class Visit(BaseModel):
    """Visit model"""
    id: Optional[int] = None
    date: str
    description: str
    petId: Optional[int] = None


class Owner(BaseModel):
    """Owner model"""
    id: Optional[int] = None
    firstName: str
    lastName: str
    address: str
    city: str
    telephone: str
    pets: Optional[List[Pet]] = []


class Specialty(BaseModel):
    """Veterinarian specialty model"""
    id: int
    name: str


class Vet(BaseModel):
    """Veterinarian model"""
    id: Optional[int] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    specialties: Optional[List[Specialty]] = []


class PetRequest(BaseModel):
    """Request model for adding a pet"""
    name: str
    birthDate: str
    typeId: int = Field(..., description="Pet type ID: 1=cat, 2=dog, 3=lizard, 4=snake, 5=bird, 6=hamster")


class AddPetRequest(BaseModel):
    """Request model for adding a pet to an owner"""
    pet: PetRequest
    ownerId: int


class OwnerRequest(BaseModel):
    """Request model for adding an owner"""
    firstName: str
    lastName: str
    address: str
    city: str
    telephone: str = Field(..., pattern=r'^\d{10}$', description="10-digit phone number")


class ChatRequest(BaseModel):
    """Chat request model"""
    query: str


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str

