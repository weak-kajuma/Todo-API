from typing import Optional, List, Any
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr, UUID4
import motor.motor_asyncio
import uuid
import os

app = FastAPI()

mongodb_URL = os.environ['MONGODB_URL']
client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_URL)
db = client["Todo-app"]

class Task(BaseModel):
    task_id: UUID4
    user_id: UUID4
    task_data: dict = Field(None, example={"id": 1, "title": "Hello World", "message": "Good Morning"})

class CreateTask(BaseModel):
    task_data: dict = Field(None, example={"id": 1, "title": "Hello World", "message": "Good Morning"})

class InsertTask(BaseModel):
    task_id: str
    user_id: str
    task_data: dict = Field(None, example={"id": 1, "title": "Hello World", "message": "Good Morning"})

class User(BaseModel):
    user_id: UUID4
    username: str = Field(None, example="kajuma")
    full_name: Optional[str] = Field(None, example="weak kajuma")
    email: EmailStr
    task_ids: Optional[List[str]]

class CreateUser(BaseModel):
    username: str = Field(None, example="kajuma")
    full_name: Optional[str] = Field(None, example="weak kajuma")
    email: EmailStr

class CreateUserResponse(BaseModel):
    user_id: UUID4
    username: str = Field(None, example="kajuma")
    full_name: Optional[str] = Field(None, example="weak kajuma")
    email: EmailStr

class InsertUser(BaseModel):
    user_id: str
    username: str = Field(None, example="kajuma")
    full_name: Optional[str] = Field(None, example="weak kajuma")
    email: EmailStr

@app.get("/user/{user_id}", response_model=User)
async def get_user(user_id: UUID4):
    try:
        result = await db.users.find_one({'user_id': str(user_id)})
        if result:
            return User(**result)
        else:
            raise HTTPException(status_code=404, detail="The user you are looking for was not found.")
    except HTTPException as error:
        raise error
    except:
        raise HTTPException(status_code=500)

@app.post("/user", response_model=CreateUserResponse)
async def create_user(user_body: CreateUser):
    try:
        user_id = str(uuid.uuid4())
        await db.users.insert_one(InsertUser(user_id=user_id, **user_body.dict()).dict())
        result = await db.users.find_one({'user_id': user_id})
        return CreateUserResponse(**result) 
    except:
        raise HTTPException(status_code=500)

@app.put("/user/{user_id}", response_model=User)
async def update_user(user_id: UUID4, user_body: CreateUser):
    try:
        result = await db.users.find_one({'user_id': str(user_id)})
        if not result:
            raise HTTPException(status_code=404, detail="The user you are looking for was not found.")
        await db.users.update_one({'user_id': str(user_id)}, {'$set': user_body.dict()})
        return User(**await db.users.find_one({'user_id': str(user_id)}))
    except HTTPException as error:
        raise error        
    except:
        raise HTTPException(status_code=500)

@app.delete("/user/{user_id}", status_code=204)
async def disable_user(user_id: UUID4):
    try:
        await db.users.delete_one({'user_id': str(user_id)})
    except:
        raise HTTPException(status_code=500)

@app.get("/task/{task_id}", response_model=Task)
async def get_task(task_id: UUID4):
    try:
        result = await db.tasks.find_one({'task_id': str(task_id)})
        print(result)
        if result:
            return Task(**result)
        else: 
            raise HTTPException(status_code=404, detail="The task you are looking for was not found.")
    except HTTPException as error:
        raise error
    except:
        raise HTTPException(status_code=500)

@app.post("/task/{user_id}", response_model=Task)
async def create_task(user_id: UUID4, task_body: CreateTask):
    try:
        task_id = str(uuid.uuid4())

        user = await db.users.find_one({"user_id": str(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="The user you are looking for was not found.")
        user["task_ids"].append(task_id)
        await db.users.update_one({"user_id": str(user_id)}, {"$set": user})

        task = InsertTask(task_id=task_id, user_id=str(user_id), task_data=task_body.task_data).dict()
        await db.tasks.insert_one(task)
        result = await db.tasks.find_one({"task_id": task["task_id"]})

        return Task(**result)
    except HTTPException as error:
        raise error
    except:
        raise HTTPException(status_code=500)

@app.put("/task/{task_id}", response_model=Task)
async def update_task(task_id: UUID4, task_body: CreateTask):
    try:
        result = await db.tasks.find_one({'task_id': str(task_id)})
        if not result:
            raise HTTPException(status_code=404, detail="The task you are looking for was not found.")
        await db.tasks.update_one({'task_id': str(task_id)}, {'$set': task_body.dict()})
        return Task(**await db.tasks.find_one({'task_id': str(task_id)}))
    except HTTPException as error:
        raise error
    except:
        raise HTTPException(status_code=500)

@app.delete("/task/{task_id}", status_code=204)
async def delete_task(task_id: UUID4):
    try:
        user = await db.users.find_one({'task_ids': {'$in': [str(task_id)]}})
        if not user:
            raise HTTPException(status_code=404, detail="The task you are looking for was not found.")
        print(user["task_ids"])
        user["task_ids"].remove(str(task_id))
        await db.users.update_one({'task_ids': {'$in': [str(task_id)]}}, {'$set': user})
        await db.tasks.delete_one({'task_id': str(task_id)})
    except HTTPException as error:
        raise error
    except:
        raise HTTPException(status_code=500)
