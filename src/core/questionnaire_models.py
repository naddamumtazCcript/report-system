"""
Pydantic models for questionnaire JSON validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any


class QuestionnaireAnswers(BaseModel):
    """Nested answers object from questionnaire JSON"""
    
    # Personal Info
    legalFirstName: Optional[str] = ""
    lastName: Optional[str] = ""
    street: Optional[str] = ""
    unit: Optional[str] = ""
    city: Optional[str] = ""
    stateProvince: Optional[str] = ""
    postalCode: Optional[str] = ""
    homePhone: Optional[str] = ""
    mobilePhone: Optional[str] = ""
    email: Optional[str] = ""
    dateOfBirth: Optional[str] = ""
    gender: Optional[str] = ""
    relationshipStatus: Optional[str] = ""
    occupation: Optional[str] = ""
    hoursPerWeek: Optional[str] = ""
    currentWeight: Optional[str] = ""
    height: Optional[str] = ""
    
    # Health Info
    officialDiagnosis: Optional[str] = ""
    healthHistoryDetails: Optional[str] = ""
    wellnessStruggles: Optional[str] = ""
    wellnessExcitement: Optional[str] = ""
    currentSupplements: Optional[str] = ""
    prescriptionMedications: Optional[str] = ""
    allergies: Optional[str] = ""
    workedWithCoach: Optional[str] = ""
    
    # Diet History (nested JSON strings)
    threeDayFoodLog: Optional[str] = ""
    threeDayMacros: Optional[str] = ""
    
    # Nutrition Preferences
    nutritionSupportType: Optional[str] = ""
    nutritionPreference: Optional[str] = ""
    nutritionStruggles: Optional[str] = ""
    recipePreference: Optional[str] = ""
    macroBreakdowns: Optional[str] = ""
    foodsAvoided: Optional[str] = ""
    
    # Fitness
    workoutWeek: Optional[str] = ""
    workoutLimitations: Optional[str] = ""
    
    # Digestive Health
    digestiveSymptoms: Optional[str] = ""
    bowelFrequency: Optional[str] = ""
    bowelOther: Optional[str] = ""
    bristolType: Optional[str] = ""
    cycleRegularity: Optional[str] = ""
    
    # Lifestyle
    energyLevels: Optional[str] = ""
    sleepQuality: Optional[str] = ""
    birthControlHistory: Optional[str] = ""
    mentalHealthStruggles: Optional[str] = ""
    mentalHealthSupport: Optional[str] = ""
    eatingDisorderHistory: Optional[str] = ""
    alcoholFrequency: Optional[str] = ""
    additionalSymptoms: Optional[str] = ""
    typicalDay: Optional[str] = ""
    
    # Medical History
    highBloodPressure: Optional[str] = ""
    hormonalBirthControl: Optional[str] = ""
    moldExposure: Optional[str] = ""
    longTermAntibiotics: Optional[str] = ""
    familyEstrogenCancer: Optional[str] = ""
    familyHistoryDetails: Optional[str] = ""
    
    # Personal Care
    skincareProducts: Optional[str] = ""
    hairColorTreatment: Optional[str] = ""
    heatUsage: Optional[str] = ""
    fertilityJourney: Optional[str] = ""
    
    # Supplement Preferences
    supplementPreference: Optional[str] = ""
    
    class Config:
        extra = "allow"  # Allow extra fields not defined


class QuestionnaireJSON(BaseModel):
    """Main questionnaire JSON structure"""
    answers: QuestionnaireAnswers
    
    class Config:
        extra = "allow"
