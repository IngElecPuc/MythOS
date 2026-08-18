from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from src.integrations.dependencies import SessionDep
from src.schemas.auth import Users, UserCreateIn, UserCreateOut, UserRead, UserUpdateIn, UserReplaceIn
from src.services.auth import encode_token, Token
from src.services.auth import hash_password, verify_password
from sqlmodel import select

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.get("/", response_model=UserRead)
async def get_accounts(current_user:Token, db: SessionDep) -> list[UserRead]:
    query = select(Users)
    accounts = db.exec(query).all()
    users = []
    for account in accounts:
        users.append(UserRead(
            id=account.id, 
            username=account.username, 
            email=account.email))
    
    return users

@auth_router.get("/me", response_model=UserRead)
def profile(current_user:Token, ):
    return current_user

@auth_router.get("/{id}", response_model=UserRead)
async def get_account(db: SessionDep, id: int) -> Users:
    query = select(Users).where(Users.id == id)
    account = db.exec(query).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return account.model_dump()

@auth_router.post("/signin", response_model=UserCreateOut, response_class=JSONResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreateIn, db: SessionDep) -> UserCreateOut:
    # Aquí puedes agregar la lógica para crear un nuevo usuario en la base de datos
    
    password_hash = hash_password(user_in.password)  
    user = Users(
        username=user_in.username,
        email=user_in.email,
        password_hash=password_hash 
    )

    #user = Users(**user_in.dict())  # Crea un nuevo usuario a partir del modelo de entrada
    db.add(user)
    db.commit()
    db.refresh(user)
    #return UserCreateOut(id=user.id, username=user.username, email=user.email)
    return user.model_dump()

@auth_router.put("/{id}", response_model=UserRead)
async def replace_account(
    db: SessionDep,
    id: int,
    user_in: UserReplaceIn,
    current_user: Token
):
    account = db.get(Users, id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    account.username = user_in.username
    account.email = user_in.email
    account.password_hash = hash_password(user_in.password)

    db.add(account)
    db.commit()
    db.refresh(account)

    return account

@auth_router.patch("/{id}", response_model=UserRead)
async def partial_update_account(
    db: SessionDep, 
    id: int, 
    user_in: UserUpdateIn,
    current_user: Token
    ) -> Users:
    query = select(Users).where(Users.id == id)
    account = db.exec(query).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )    # Actualiza los campos del usuario con los datos proporcionados
    
    update_data = user_in.model_dump(exclude_unset=True)  # PATCH: solo lo que llegó
    
    if "password" in update_data:
        plain_password = update_data.pop("password")
        update_data["password_hash"] = hash_password(plain_password)

    for key, value in update_data.items():
        setattr(account, key, value)
    
    db.add(account)
    db.commit()
    db.refresh(account)
    return account.model_dump()

@auth_router.delete("/{id}")#, status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(db: SessionDep, id: int) -> dict:
    query = select(Users).where(Users.id == id)
    account = db.exec(query).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db.delete(account)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@auth_router.post("/login")
#async def login(user_in: UserCreateIn, db: SessionDep) -> str:
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: SessionDep,
    ) -> dict:
    query = select(Users).where(Users.username == form_data.username)
    account = db.exec(query).first()
    if not account or not verify_password(form_data.password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = encode_token(account.id, account.username, account.email)

    return {"access_token": token}