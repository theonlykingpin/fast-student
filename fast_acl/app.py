from contextlib import asynccontextmanager
from typing import Callable, Type

import uvicorn
from fastapi import APIRouter, Body, Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse

from fast_acl.acl.mapper import (
    PermissionGrants,
    UserRoles,
    get_permission_callable,
    get_permission_setting,
)
from fast_acl.acl.routes import RoutesEnum
from fast_acl.auth import TokenData, check_auth, create_access_token
from fast_acl.controller import StudentController
from fast_acl.db import Database
from fast_acl.exception import NotFoundError
from fast_acl.sample_data import add_sample_data
from fast_acl.schema import ProtectedMessage, StudetnInput, Token
from fast_acl.settings import ProductEnvironment, setting
from fast_acl.types import ClassRoomId, StudentId


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: This should be a script, not a lifespan. for sake of simplicity, we did this!
    if setting.ENV != ProductEnvironment.PRODUCTION:
        add_sample_data()
    yield


app = FastAPI(lifespan=lifespan)


def get_database():
    return Database
    # return Database


router = APIRouter()


@app.exception_handler(NotFoundError)
async def unicorn_exception_handler(_: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": f"Object with id {exc.obj_id} was nout found"},
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(payload: TokenData):
    access_token = create_access_token(data=payload)
    return {"access_token": access_token}


@router.get(
    "/protected-route",
    dependencies=[Depends(check_auth)],
    response_model=ProtectedMessage,
)
async def read_protected_route():
    return ProtectedMessage(message="You have access to this protected route!")


@router.post("/classroom/{classroom_id}/student")
async def create_student(
    classroom_id: ClassRoomId,
    token: TokenData = Depends(check_auth),
    database: Type[Database] = Depends(get_database),
    permission_callable: Callable = Depends(get_permission_callable),
    permission_setting: dict[RoutesEnum, dict[UserRoles, PermissionGrants]] = Depends(
        get_permission_setting
    ),
    body: StudetnInput = Body(),
):
    await permission_callable(
        user_rule=token.role,
        user_id=token.user_id,
        route=RoutesEnum.ADD_STUDENT,
        permission_setting=permission_setting,
        classroom_id=classroom_id,
    )
    StudentController(database).add_student(
        **body.model_dump(), classroom_id=classroom_id
    )


@router.get("/classroom/{classroom_id}/student/{student_id}")
async def get_student(
    classroom_id: ClassRoomId,
    student_id: StudentId,
    token: TokenData = Depends(check_auth),
    database: Type[Database] = Depends(get_database),
    permission_callable: Callable = Depends(get_permission_callable),
    permission_setting: dict[RoutesEnum, dict[UserRoles, PermissionGrants]] = Depends(
        get_permission_setting
    ),
):
    await permission_callable(
        user_rule=token.role,
        user_id=token.user_id,
        route=RoutesEnum.READ_STUDENT,
        permission_setting=permission_setting,
        classroom_id=classroom_id,
    )
    StudentController(database).get_student(student_id)


@router.put("/classroom/{classroom_id}/student/{student_id}")
async def update_student(
    classroom_id: ClassRoomId,
    student_id: StudentId,
    token: TokenData = Depends(check_auth),
    database: Type[Database] = Depends(get_database),
    permission_callable: Callable = Depends(get_permission_callable),
    permission_setting: dict[RoutesEnum, dict[UserRoles, PermissionGrants]] = Depends(
        get_permission_setting
    ),
):
    await permission_callable(
        user_rule=token.role,
        user_id=token.user_id,
        route=RoutesEnum.UPDATE_STUDENT,
        permission_setting=permission_setting,
        classroom_id=classroom_id,
    )
    StudentController(database).update_student_grade(student_id, grade=10)


@router.delete("/classroom/{classroom_id}/student/{student_id}")
async def delete_student(
    classroom_id: ClassRoomId,
    student_id: StudentId,
    token: TokenData = Depends(check_auth),
    database: Type[Database] = Depends(get_database),
    permission_callable: Callable = Depends(get_permission_callable),
    permission_setting: dict[RoutesEnum, dict[UserRoles, PermissionGrants]] = Depends(
        get_permission_setting
    ),
):
    await permission_callable(
        user_rule=token.role,
        user_id=token.user_id,
        route=RoutesEnum.DELETE_STUDENT,
        permission_setting=permission_setting,
        classroom_id=classroom_id,
    )


@router.patch("/classroom/{classroom_id}/student/{student_id}")
async def expel_student(
    classroom_id: ClassRoomId,
    student_id: StudentId,
    token: TokenData = Depends(check_auth),
    database: Type[Database] = Depends(get_database),
    permission_callable: Callable = Depends(get_permission_callable),
    permission_setting: dict[RoutesEnum, dict[UserRoles, PermissionGrants]] = Depends(
        get_permission_setting
    ),
):
    await permission_callable(
        user_rule=token.role,
        user_id=token.user_id,
        route=RoutesEnum.EXPEL_STUDENT,
        permission_setting=permission_setting,
        classroom_id=classroom_id,
    )
    StudentController(database).expel_student(student_id)


app.include_router(router, prefix=f"/v{setting.VERSION}")


if __name__ == "__main__":
    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=True)
