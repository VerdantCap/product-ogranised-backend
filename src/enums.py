from enum import Enum  
from typing import Optional
from fastapi import HTTPException  

# Enum class representing different statuses an item can have
class ItemStatus(str, Enum):  
    ALL = 'all'  
    ACTIVE = 'active'  
    EXPIRED = 'expired'  
    RENEWAL = 'renewal'  

    # Method to get a human-readable label for the status
    def get_label(self) -> str:  
        return self.name.replace('_', ' ').title()  

    # Method to get the scope of the status
    def scope(self):  
        return {  
            ItemStatus.ACTIVE: "active()",  
            ItemStatus.EXPIRED: "expired()",  
            ItemStatus.RENEWAL: "renewal()"  
        }.get(self, None)  

# Enum class representing different types of items
class ItemType(str, Enum):  
    CAR_INSURANCE = 'car-insurance'  
    HOME_INSURANCE = 'home-insurance'  
    LIFE_INSURANCE = 'life-insurance'  
    PET_INSURANCE = 'pet-insurance'  
    TRAVEL_INSURANCE = 'travel-insurance'  
    
    UTILITIES = 'utilities'  
    COUNCIL_TAX = 'council-tax'  
    BROADBAND = 'broadband'  
    MOBILE_PHONE = 'mobile-phone'  
    
    MORTGAGE = 'mortgage'  
    CREDIT_CARD = 'credit-card'  
    SAVINGS = 'savings'  
    PENSION = 'pension'  
    VEHICLE_FINANCE = 'vehicle-finance'  
    CURRENT_ACCOUNT = 'current-account'  
    
    ANIMAL = 'animal'  
    
    HOLIDAY = 'holiday'  
    VISA = 'visa'  
    PASSPORT = 'passport'  
    
    CAR = 'car'  
    MOTORBIKE = 'motorbike'  
    COMMERCIAL_VEHICLE = 'commercial-vehicle'  
    OTHER_VEHICLE = 'other-vehicle'  

    BIRTHDAY_PARTY = 'birthday-party'  
    DINNER_PARTY = 'dinner-party'  
    CHRISTENING = 'christening'  
    WEDDING = 'wedding'  
    FUNERAL = 'funeral'  

    # Method to get the icon associated with the item type
    def get_icon(self) -> Optional[str]:  
        icon_map = {  
            ItemType.CAR_INSURANCE: 'fas-car-crash',  
            ItemType.HOME_INSURANCE: 'fas-home',  
            ItemType.LIFE_INSURANCE: 'fas-user-injured',  
            ItemType.PET_INSURANCE: 'fas-shield-cat',  
            ItemType.TRAVEL_INSURANCE: 'fas-plane-lock',  
            ItemType.ANIMAL: 'fas-dog',  
            ItemType.UTILITIES: 'fas-glass-water-droplet',  
            ItemType.COUNCIL_TAX: 'fas-building-user',  
            ItemType.BROADBAND: 'fas-wifi',  
            ItemType.MOBILE_PHONE: 'fas-mobile-alt',  
            ItemType.CAR: 'fas-car-side',  
            ItemType.VEHICLE_FINANCE: 'fas-car-side',  
            ItemType.MOTORBIKE: 'fas-motorcycle',  
            ItemType.OTHER_VEHICLE: 'fas-caravan',  
            ItemType.COMMERCIAL_VEHICLE: 'fas-truck',  
            ItemType.MORTGAGE: 'fas-hand-holding-dollar',  
            ItemType.SAVINGS: 'fas-piggy-bank',  
            ItemType.PENSION: 'fas-person-cane',  
            ItemType.CURRENT_ACCOUNT: 'fas-wallet',  
            ItemType.HOLIDAY: 'fas-umbrella-beach',  
            ItemType.PASSPORT: 'fas-passport',  
            ItemType.VISA: 'fas-address-card',  
            ItemType.BIRTHDAY_PARTY: 'fas-cake-candles',  
            ItemType.DINNER_PARTY: 'fas-champagne-glasses',  
            ItemType.CHRISTENING: 'fas-baby-carriage',  
            ItemType.WEDDING: 'fas-gem',  
            ItemType.FUNERAL: 'fas-cross'  
        }  
        return icon_map.get(self, 'iconsax-bul-box-1')  

    # Method to get a human-readable label for the item type
    def get_label(self) -> str:  
        return self.name.replace('_', ' ').title()  

# Enum class representing different steps in a user profile
class ProfileStep(str, Enum):  
    CREATE_TASK = 'create-task'  
    CREATE_ITEM = 'create-item'  
    CREATE_EVENT = 'create-event'  
    INVITE_MEMBERS = 'invite-members'  

    # Method to get a human-readable label for the profile step
    def get_label(self) -> str:  
        return self.name.replace('_', ' ').title()  

    # Method to get the URL associated with the profile step
    def get_url(self) -> Optional[str]:  
        url_map = {  
            ProfileStep.CREATE_EVENT: '/events/create',  
            ProfileStep.CREATE_TASK: '/tasks/create',  
            ProfileStep.INVITE_MEMBERS: '/members/invite',  
        }  
        return url_map.get(self, None)  

# Enum class representing different types of files
class FileType(str, Enum):  
    CERTIFICATE = 'certificate'  
    POLICY = 'policy'  
    PASSPORT = 'passport'  
    VISA = 'visa'  
    MOT = 'mot'  
    SERVICES = 'services'  
    TAX = 'tax'  
    PHOTO = 'photo'  
    QUOTE = 'quote'  

# Enum class representing different billing plans
class BillingPlan(str, Enum):  
    STANDARD = 'standard'  

# Enum class representing different item spaces
class ItemSpace(str, Enum):  
    INSURANCE = 'insurance'  
    HOUSEHOLD = 'household'  
    FINANCE = 'finance'  
    PETS = 'pets'  
    PERSONAL_DOCUMENTS = 'personal_documents'  
    VEHICLES = 'vehicles'  
    TRAVEL = 'travel'  
    SPECIAL_EVENTS = 'special_events'
    
    # Method to get the class instance associated with the item space
    def class_instance(self):
        class_name = f"{self.name.capitalize()}ItemSpace"  
        if class_name in globals(): 
            return globals()[class_name]()  
        else:  
            raise HTTPException(status_code=500, detail=f"Class {class_name} does not exist")  

    # Static method to convert item spaces to a select array
    @staticmethod  
    def to_select_array():  
        items = {}  
        for case in ItemSpace:  
            try:  
                items[case.value] = case.class_instance().title()  
            except HTTPException as e:
                print(e.detail)  
        return items
