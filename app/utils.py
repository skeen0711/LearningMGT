from lib2to3.pytree import Base

import
from sqlalchemy import Column

...

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    attempts = relationship(
        'UserCourseAttempt',
        back_populates= 'user'
    )

class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    filepath = Column(String) # Path to .elp file
    attempts = relationship(
        'UserCourseAttempt',
        back_populates= 'course'
    )

class UserCourseAttempt(Base):
    __tablename__ = "user_course_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    correct_answers = Column(Integer)
    total_questions = Column(Integer)
    passed = Column(Boolean)

    user = relationship("User", back_populates="attempts")
    course = relationship("Course", back_populates="attempts")

