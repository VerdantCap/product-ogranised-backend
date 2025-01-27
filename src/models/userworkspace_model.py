# from sqlalchemy import String, ForeignKey
# from sqlalchemy.orm import Mapped,mapped_column, relationship
# from sqlalchemy.dialects.postgresql import JSONB
# from base import Base
# from enums import ProfileStep

# class UserWorkspace(Base):  
#     __tablename__ = 'user_workspaces'  
    
#     user_id: Mapped[str]= mapped_column(String, ForeignKey('users.id'), primary_key=True)  
#     workspace_id: Mapped[str]= mapped_column(String, ForeignKey('workspaces.id'), primary_key=True)  
#     profile_completion: Mapped[list] = mapped_column(JSONB, nullable=False)

#     user = relationship("User", back_populates="userworkspace")  
#     workspace = relationship("Workspace", back_populates="userworkspace")  

#     def is_owner(self, user_id: int) -> bool:  
#         return self.user_id == user_id  

#     def has_completed(self, step: ProfileStep) -> bool:  
#         return self.profile_completion.get(step.value, 0) == 1  

#     def has_cleared(self, step: ProfileStep) -> bool:  
#         return self.profile_completion.get(step.value, 1) == 0  

#     def is_outstanding(self, step: ProfileStep) -> bool:  
#         return step.value not in self.profile_completion  

#     def complete_step(self, step: ProfileStep) -> None:  
#         if step.value not in self.profile_completion:  
#             self.profile_completion[step.value] = 1  


#     def clear_step(self, step: ProfileStep) -> None:  
#         self.profile_completion[step.value] = 0  

#     def profile_percentage(self) -> int:  
#         steps = ProfileStep.__members__.values()  
#         completed = sum(1 for step in steps if self.has_completed(step))  
#         total_steps = len(steps)  
#         return 100 if total_steps == 0 else round((completed / total_steps) * 100) 